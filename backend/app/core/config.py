from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-First CRM"
    API_V1_STR: str = "/api/v1"
    
    # LLM Settings
    GROQ_API_KEY: Optional[str] = None
    MODEL_NAME: str = "llama-3.1-8b-instant"
    
    # Database (Placeholder)
    DATABASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
