from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.api.routers import router
from app.core.logging_config import setup_logging

# Set up Loguru for logging
logger = setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

@app.get("/")
async def root():
    return {
        "status": "success",
        "status_code": 200,
        "message": "Welcome to SCA Training Simulator API.",
        "data": {
            "description": "The Simulated Consultation Assessment (SCA) Training Simulator is a platform that helps GP candidates prepare for their SCA exam by providing realistic simulations to assess and improve their clinical, professional, and communication skills.",
            "docs": f"{settings.API_V1_STR}/docs"
        }
    }