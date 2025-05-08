from fastapi import APIRouter

from app.api.routers import user, consultation
from app.core.config import settings

# Create main router
router = APIRouter(prefix=settings.API_V1_STR)

# Include sub-routers
router.include_router(user.router, prefix="/users", tags=["users"])
router.include_router(consultation.router, prefix="/consultations", tags=["consultations"])
