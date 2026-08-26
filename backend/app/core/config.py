"""Application configuration settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RISK-X"
    PROJECT_DESCRIPTION: str = "AI-Powered Payment Risk Investigation and Response System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Database & Webhook Configuration
    DATABASE_PATH: str = "data/risk_x.db"
    RAZORPAY_WEBHOOK_SECRET: str = "risk_x_buildathon_secret_2026"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
