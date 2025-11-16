"""Application configuration and settings."""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Battle-D"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Magic Link Authentication
    MAGIC_LINK_EXPIRY_MINUTES: int = 15
    MAGIC_LINK_BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    # Email Configuration
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "resend")  # Options: resend, console
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@battle-d.com")

    # Session
    SESSION_COOKIE_NAME: str = "battle_d_session"
    SESSION_MAX_AGE_SECONDS: int = 86400 * 7  # 7 days

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/battle_d.db"
    )
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"


settings = Settings()
