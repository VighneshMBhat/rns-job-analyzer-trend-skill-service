from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # SERP API (for job listings)
    SERP_API_KEY: str
    
    # Apify (for Reddit scraping)
    APIFY_API_TOKEN: str
    
    # Service Config
    HOST_URL: str = "http://localhost:8002"
    
    # Default search config
    DEFAULT_REGION: str = "us"
    DEFAULT_LANGUAGE: str = "en"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
