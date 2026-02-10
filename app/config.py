from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "ReviewPulse AI API"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "production"
    
    # MongoDB Settings
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "reviewpulse_db"
    
    # LLM Settings
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # JWT Auth Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 168  # 7 days
    
    # Security
    CORS_ORIGINS: list[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()