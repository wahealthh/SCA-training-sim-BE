import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.consultation import generate_case, score_consultation
from app.db.load import load
from app.models.consultation import Consultation, PatientCase, PeerComment
from app.schema.consultation import CommentRequest, ScoreRequest
from app.core.config import settings
from loguru import logger

# Configure logging
# logger = logging.getLogger(__name__) # Old standard logging

router = APIRouter()


@router.get("/generate-case", status_code=status.HTTP_200_OK) 
async def api_generate_case(db: Session = Depends(load)):
    """Generate a new patient case for consultation"""
    try:
        case_data = generate_case()
        
        # Store the case in the database
        new_case = PatientCase(
            age=case_data["age"],
            presenting=case_data["presenting"],
            context=case_data["context"]
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        
        return case_data
    except Exception as e:
        error_detail = str(e)
        raise HTTPException(status_code=(
                e.status_code
                if hasattr(e, "status_code")
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "message": "Failed to generate case",
                "error": error_detail,
                "case": new_case.model_dump(),
            },
        )

@router.post("/score-consultation", status_code=status.HTTP_201_CREATED)  
async def api_score_consultation(request: ScoreRequest, db: Session = Depends(load)):
    """Score a completed consultation based on transcript and case details"""
    try:
        scores = score_consultation(request.transcript, request.case_details)
        
        # Find or create the patient case
        case = db.query(PatientCase).filter_by(
            age=request.case_details.age,
            presenting=request.case_details.presenting
        ).first()
        
        if not case:
            # If case doesn't exist, create it
            case = PatientCase(
                age=request.case_details.age,
                presenting=request.case_details.presenting,
                context=request.case_details.context
            )
            db.add(case)
            db.commit()
            db.refresh(case)
        
        # Store the consultation record
        consultation = Consultation(
            user_id=request.user_id,
            patient_case_id=case.id,
            transcript=request.transcript,
            overall_score=scores["overall_score"],
            feedback=scores["feedback"],
            domain_scores=scores["scores"],
            audio_recording=None,  # Will be updated later if recording exists
            duration_seconds=None
        )
        
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        
        # Return consultation ID along with scores so the frontend can attach the recording
        scores["consultation_id"] = consultation.id
        
        return scores
    except Exception as e:
        logger.exception(f"Error scoring consultation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_history(db: Session = Depends(load)):
    """Get history of consultation scores"""
    try:
        # Query all consultations with their associated patient cases
        consultations = db.query(Consultation).join(
            PatientCase
        ).order_by(Consultation.created_at.desc()).all()
        
        history = []
        for consultation in consultations:
            has_recording = consultation.audio_recording is not None
            
            # Get comment count if consultation is shared
            comment_count = 0
            if consultation.is_shared:
                comment_count = len(consultation.peer_comments)
            
            history.append({
                "id": consultation.id,
                "timestamp": consultation.created_at.isoformat(),
                "case_details": {
                    "age": consultation.patient_case.age,
                    "presenting": consultation.patient_case.presenting,
                    "context": consultation.patient_case.context
                },
                "scores": consultation.domain_scores,
                "overall_score": consultation.overall_score,
                "feedback": consultation.feedback,
                "has_recording": has_recording,
                "duration_seconds": consultation.duration_seconds if has_recording else None,
                "is_shared": consultation.is_shared,
                "comment_count": comment_count
            })
        
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        error_detail = str(e)
        raise HTTPException(status_code=(
                e.status_code
                if hasattr(e, "status_code")
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=error_detail
        )


@router.get("/vapi/call/{call_id}")
async def get_vapi_call(call_id: str):
    """
    Get call details from Vapi API
    
    This endpoint proxies requests to the Vapi API to fetch call details
    including the transcript of the conversation.
    """
    try:
        # Make request to Vapi API
        vapi_url = f"{settings.VAPI_BASE_URL}/call/{call_id}"
        headers = {
            "Authorization": f"Bearer {settings.VAPI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = httpx.get(vapi_url, headers=headers)
        if not response.ok:
            return JSONResponse(
                status_code=response.status_code,
                content={"error": f"Failed to fetch call details: {response.text}"}
            )
            
        call_data = response.json()
        logger.info(f"Retrieved call details for call ID {call_id}: {json.dumps(call_data, indent=2)}")
        
        # Extract transcript from various possible locations in the response
        transcript = []
        
        # Try different possible paths for the transcript
        if "transcript" in call_data and isinstance(call_data["transcript"], list):
            transcript = call_data["transcript"]
        elif "artifact" in call_data and "transcript" in call_data["artifact"]:
            # In older versions, transcript might be a string in artifact.transcript
            if isinstance(call_data["artifact"]["transcript"], str):
                # Try to parse the transcript string into turns
                try:
                    transcript_str = call_data["artifact"]["transcript"]
                    lines = transcript_str.strip().split("\n")
                    for line in lines:
                        if ":" in line:
                            speaker, text = line.split(":", 1)
                            speaker_role = "human" if speaker.strip().lower() == "doctor" else "assistant"
                            transcript.append({
                                "speaker": speaker_role,
                                "text": text.strip()
                            })
                except Exception as e:
                    logger.error(f"Error parsing transcript string: {e}")
                    pass
            else:
                # It might already be in a structured format
                transcript = call_data["artifact"]["transcript"]
        elif "messages" in call_data:
            # Try to extract from messages array
            for msg in call_data["messages"]:
                if "role" in msg and "message" in msg:
                    transcript.append({
                        "speaker": "human" if msg["role"] == "human" else "assistant",
                        "text": msg["message"]
                    })
        
        # If we still don't have a transcript, check if there's a messagesOpenAIFormatted field
        if not transcript and "artifact" in call_data and "messagesOpenAIFormatted" in call_data["artifact"]:
            for msg in call_data["artifact"]["messagesOpenAIFormatted"]:
                if "role" in msg and "content" in msg:
                    # Skip system messages
                    if msg["role"] != "system":
                        transcript.append({
                            "speaker": msg["role"],
                            "text": msg["content"]
                        })
        
        logger.info(f"Extracted transcript with {len(transcript)} turns")
        
        # Extract and return the relevant information
        result = {
            "call_id": call_data.get("id"),
            "status": call_data.get("status"),
            "duration": call_data.get("duration"),
            "transcript": transcript
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching Vapi call details: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Peer collaboration API routes
@router.post("/consultations/{consultation_id}/share")
async def share_consultation(consultation_id: int, db: Session = Depends(load)):
    """Share a consultation for peer review"""
    try:
        consultation = db.query(Consultation).filter_by(id=consultation_id).first()
        
        if not consultation:
            return JSONResponse(
                status_code=404,
                content={"error": "Consultation not found"}
            )
        
        consultation.is_shared = True
        db.commit()
        
        return {"status": "success", "message": "Consultation shared for peer review"}
    except Exception as e:
        logger.error(f"Error sharing consultation: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/consultations/{consultation_id}/unshare")
async def unshare_consultation(consultation_id: int, db: Session = Depends(load)):
    """Unshare a consultation from peer review"""
    try:
        consultation = db.query(Consultation).filter_by(id=consultation_id).first()
        
        if not consultation:
            return JSONResponse(
                status_code=404,
                content={"error": "Consultation not found"}
            )
        
        consultation.is_shared = False
        db.commit()
        
        return {"status": "success", "message": "Consultation removed from peer review"}
    except Exception as e:
        logger.error(f"Error unsharing consultation: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/shared-consultations")
async def get_shared_consultations(db: Session = Depends(load)):
    """Get all shared consultations for peer review"""
    try:
        consultations = db.query(Consultation).filter_by(is_shared=True).join(
            PatientCase
        ).order_by(Consultation.created_at.desc()).all()
        
        shared = []
        for consultation in consultations:
            has_recording = consultation.audio_recording is not None
            
            shared.append({
                "id": consultation.id,
                "timestamp": consultation.created_at.isoformat(),
                "case_details": {
                    "age": consultation.patient_case.age,
                    "presenting": consultation.patient_case.presenting,
                    "context": consultation.patient_case.context
                },
                "scores": consultation.domain_scores,
                "overall_score": consultation.overall_score,
                "feedback": consultation.feedback,
                "has_recording": has_recording,
                "duration_seconds": consultation.duration_seconds if has_recording else None,
                "comment_count": len(consultation.peer_comments)
            })
        
        return {"shared_consultations": shared}
    except Exception as e:
        logger.error(f"Error retrieving shared consultations: {e}")
        return {"error": str(e)}, 500

@router.post("/consultations/{consultation_id}/comments")
async def add_comment(consultation_id: int, comment_request: CommentRequest, db: Session = Depends(load)):
    """Add a comment to a shared consultation"""
    try:
        consultation = db.query(Consultation).filter_by(id=consultation_id).first()
        
        if not consultation:
            return JSONResponse(
                status_code=404,
                content={"error": "Consultation not found"}
            )
        
        if not consultation.is_shared:
            return JSONResponse(
                status_code=403,
                content={"error": "Consultation is not shared for peer review"}
            )
        
        # Create new comment
        comment = PeerComment(
            consultation_id=consultation_id,
            user_id=comment_request.user_id,
            comment=comment_request.comment
        )
        
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        return {
            "status": "success",
            "comment_id": comment.id,
            "created_at": comment.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/consultations/{consultation_id}/comments")
async def get_comments(consultation_id: int, db: Session = Depends(load)):
    """Get all comments for a shared consultation"""
    try:
        consultation = db.query(Consultation).filter_by(id=consultation_id).first()
        
        if not consultation:
            return JSONResponse(
                status_code=404,
                content={"error": "Consultation not found"}
            )
        
        comments = []
        for comment in consultation.peer_comments:
            # Get the username for the comment if available
            username = "Anonymous"
            if comment.user:
                username = comment.user.username
                
            comments.append({
                "id": comment.id,
                "user_id": comment.user_id,
                "username": username,
                "comment": comment.comment,
                "created_at": comment.created_at.isoformat()
            })
        
        return {"comments": comments}
    except Exception as e:
        logger.error(f"Error retrieving comments: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Admin API Routes
@router.get("/admin/stats")
async def get_admin_stats(db: Session = Depends(load)):
    """Get database statistics for admin dashboard"""
    try:
        user_count = db.query(User).count()
        case_count = db.query(PatientCase).count()
        consultation_count = db.query(Consultation).count()
        
        return {
            "user_count": user_count,
            "case_count": case_count,
            "consultation_count": consultation_count
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return {"error": str(e)}, 500

@router.get("/admin/cases")
async def get_admin_cases(db: Session = Depends(load)):
    """Get recent patient cases for admin dashboard"""
    try:
        cases = db.query(PatientCase).order_by(
            PatientCase.created_at.desc()
        ).limit(10).all()
        
        return {
            "cases": [
                {
                    "id": case.id,
                    "age": case.age,
                    "presenting": case.presenting,
                    "context": case.context,
                    "created_at": case.created_at.isoformat()
                }
                for case in cases
            ]
        }
    except Exception as e:
        logger.error(f"Error getting admin cases: {e}")
        return {"error": str(e)}, 500

@router.get("/admin/consultations")
async def get_admin_consultations(db: Session = Depends(load)):
    """Get recent consultations for admin dashboard"""
    try:
        consultations = db.query(Consultation).join(
            PatientCase
        ).order_by(
            Consultation.created_at.desc()
        ).limit(10).all()
        
        return {
            "consultations": [
                {
                    "id": consultation.id,
                    "patient_case_id": consultation.patient_case_id,
                    "patient_presenting": consultation.patient_case.presenting,
                    "overall_score": consultation.overall_score,
                    "created_at": consultation.created_at.isoformat()
                }
                for consultation in consultations
            ]
        }
    except Exception as e:
        logger.error(f"Error getting admin consultations: {e}")
        return {"error": str(e)}, 500

@router.get("/admin/test-openai")
async def test_openai_connection():
    """Test OpenAI connection"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        models = client.models.list()
        
        return {
            "status": "success",
            "model": "gpt-4o"
        }
    except Exception as e:
        logger.error(f"Error testing OpenAI connection: {e}")
        return {"error": str(e)}, 500

@router.get("/admin/test-vapi")
async def test_vapi_connection():
    """Test Vapi connection"""
    try:
        # This is a simulation since we don't have direct Vapi API access in this context
        assistant_id = settings.ASSISTANT_ID
        
        if not assistant_id or assistant_id == "unknown":
            raise Exception("Assistant ID not configured")
        
        return {
            "status": "success",
            "assistant_id": assistant_id[:5] + "..." + assistant_id[-5:] if len(assistant_id) > 10 else assistant_id
        }
    except Exception as e:
        logger.error(f"Error testing Vapi connection: {e}")
        return {"error": str(e)}, 500