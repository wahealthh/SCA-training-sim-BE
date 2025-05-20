from fastapi import APIRouter

from app.api.routers import user, consultation, case, admin
from app.core.config import settings

# Create main router
router = APIRouter(prefix=settings.API_V1_STR)

# Include sub-routers
router.include_router(user.router)
router.include_router(consultation.router)
router.include_router(case.router)
router.include_router(admin.router)