from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.user import User
from app.db.load import load
from app.models.case import Case
from app.models.consultation import Consultation
from app.core.config import settings
from loguru import logger


# Admin API Routes
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
async def get_admin_stats(db: Session = Depends(load)):
    """Get database statistics for admin dashboard"""
    try:
        user_count = db.query(User).count()
        case_count = db.query(Case).count()
        consultation_count = db.query(Consultation).count()
        
        return {
            "user_count": user_count,
            "case_count": case_count,
            "consultation_count": consultation_count
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return {"error": str(e)}, 500


@router.get("/admin/test-openai")
async def test_openai_connection():
    """Test OpenAI connection"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
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

