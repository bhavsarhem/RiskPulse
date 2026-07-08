import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkeyriskpulsetestkey1234567890"  # In production, this must be a secure random key
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    PROJECT_NAME: str = "RiskPulse Enterprise Credit Default Platform"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "riskpulse"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str = ""

    # Celery & Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"

    class Config:
        case_sensitive = True
        env_file = ".env"

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Check if environment has standard POSTGRES variables set
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")
        # Default fallback to sqlite for easy local development without postgres
        return "sqlite:///./riskpulse.db"

    @property
    def get_celery_broker_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

settings = Settings()
