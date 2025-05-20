from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "SCA Training Simulator Backend"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Backend API for SCA Training Simulator"
    
    # API configuration
    API_V1_STR: str = "/api/v1"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000"]

    # Logging settings
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
        
    # Database settings
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_NAME: str = Field(..., env="DB_NAME")
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: str = Field(..., env="DB_PORT")
    DB_SSLMODE: str = Field("prefer", env="DB_SSLMODE")
    
    
    # VAPI settings
    ASSISTANT_ID: str = Field(..., env="ASSISTANT_ID")
    VAPI_API_KEY: str = Field(..., env="VAPI_API_KEY")
    
    # Authentication service settings
    AUTH_SERVICE_URL: str = "https://auth.wahealth.co.uk"
    AUTH_TOKEN_URL: str = "/auth/token"
    AUTH_VERIFY_TOKEN_URL: str = "/auth/verify_token"
    AUTH_REGISTER_URL: str = "/auth/register"
    
    # VAPI settings
    VAPI_BASE_URL: str = "https://api.vapi.ai/"
    
    # Security
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 