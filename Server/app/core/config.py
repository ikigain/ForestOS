from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    # API
    PROJECT_NAME: str = "ForestOS API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    ASYNC_DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Perenual API
    PERENUAL_API_KEY: str = "your-api-key-here"
    PERENUAL_API_BASE_URL: str = "https://perenual.com/api"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
