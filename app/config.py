from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Feedback System API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    
    # MongoDB Settings
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "feedback_db"
    
    # LLM Settings
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Security
    CORS_ORIGINS: list[str] = ["*"]  # Restrict in production
    API_KEY: str  # For admin dashboard auth
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()