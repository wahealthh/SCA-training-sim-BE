import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.consultation import generate_case, score_consultation
from app.db.load import load
from app.models.case import Case
from app.models.consultation import Consultation, PeerComment
from app.schema.consultation import CommentRequest, ScoreRequest
from app.core.config import settings
from loguru import logger


router = APIRouter(prefix="/consultations", tags=["consultations"])


@router.post("/score_consultation", status_code=status.HTTP_201_CREATED)  
async def score_consultation_route(request: ScoreRequest, db: Session = Depends(load)):
    """Score a completed consultation based on transcript and case details"""
    try:
        scores = score_consultation(request.transcript, request.case_details)
        
        # Find or create the case
        case = db.query(Case).filter_by(
            case_number=request.case_details.case_number
        ).first()
        
        if not case:
            # If case doesn't exist, create it
            case = Case(
                case_number=request.case_details.case_number,
                patient_name=request.case_details.patient_name,
                patient_age=request.case_details.patient_age,
                presenting_complaint=request.case_details.presenting_complaint,
                notes=request.case_details.notes
            )
            db.add(case)
            db.commit()
            db.refresh(case)
        
        consultation = Consultation(
            user_id=request.user_id,
            case_id=case.id,
            transcript=request.transcript,
            overall_score=scores["overall_score"],
            feedback=scores["feedback"],
            domain_scores=scores["scores"],
            coverage_analysis=scores["coverage_analysis"],
            audio_recording=None, 
            duration_seconds=None
        )
        
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        
        scores["consultation_id"] = consultation.id
        
        return scores
    except Exception as e:
        logger.exception(f"Error scoring consultation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/{user_id}", status_code=status.HTTP_200_OK)
async def get_history(user_id: str, db: Session = Depends(load)):
    """Get history of consultation scores for a specific user"""
    try:
        consultations = db.query(Consultation).filter(
            Consultation.user_id == user_id
        ).join(
            Case
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
                    "case_number": consultation.case.case_number,
                    "patient_name": consultation.case.patient_name,
                    "patient_age": consultation.case.patient_age,
                    "presenting_complaint": consultation.case.presenting_complaint,
                    "notes": consultation.case.notes
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
@router.post("/{consultation_id}/share")
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

@router.post("/{consultation_id}/unshare")
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

@router.get("/shared_consultations")
async def get_shared_consultations(db: Session = Depends(load)):
    """Get all shared consultations for peer review"""
    try:
        consultations = db.query(Consultation).filter_by(is_shared=True).join(
            Case
        ).order_by(Consultation.created_at.desc()).all()
        
        shared = []
        for consultation in consultations:
            has_recording = consultation.audio_recording is not None
            
            shared.append({
                "id": consultation.id,
                "timestamp": consultation.created_at.isoformat(),
                "case_details": {
                    "case_number": consultation.case.case_number,
                    "patient_name": consultation.case.patient_name,
                    "patient_age": consultation.case.patient_age,
                    "presenting_complaint": consultation.case.presenting_complaint,
                    "notes": consultation.case.notes
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

@router.post("/{consultation_id}/comments")
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

@router.get("/{consultation_id}/comments")
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


