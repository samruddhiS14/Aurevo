from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aurevo API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    database_url: str
    REDIS_URL: str = "redis://localhost:6379/0"
    MILESTONE_REVIEW_HOURS: int = Field(default=72, ge=1, le=720)
    MILESTONE_REMINDER_HOURS: str = "24,48"
    MILESTONE_REMINDER_MINUTES: str = ""
    MILESTONE_REVIEW_MINUTES: int = Field(default=0, ge=0, le=10080)
    CELERY_TASK_ALWAYS_EAGER: bool = False

    JWT_SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Gemini configuration fields
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_TIMEOUT_SECONDS: float = Field(default=12.0, ge=1.0, le=60.0)
    GEMINI_MAX_ATTEMPTS: int = Field(default=2, ge=1, le=4)

    # PayPal configuration fields
    PAYPAL_CLIENT_ID: str | None = None
    PAYPAL_CLIENT_SECRET: str | None = None
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_WEBHOOK_ID: str | None = None
    PAYPAL_RETURN_URL: str = "http://localhost:5173/paypal/success"
    PAYPAL_CANCEL_URL: str = "http://localhost:5173/paypal/cancel"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()