from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Research API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered research API"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # API Keys
    OPENAI_API_KEY: str
    BING_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    SERPAPI_API_KEY: str = ""
    
    # Research Settings
    MAX_RESEARCH_DEPTH: int = 3
    MAX_SOURCES: int = 10
    DEFAULT_RESEARCH_DEPTH: int = 1
    
    # Search API Settings
    GOOGLE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    
    # Search Provider Configuration
    DEFAULT_SEARCH_PROVIDER: str = "google"
    MAX_SEARCH_RESULTS: int = 10
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings() 