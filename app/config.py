"""Application configuration and settings."""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Battle-D"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Application Base URL
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    # Magic Link Authentication
    MAGIC_LINK_EXPIRY_MINUTES: int = 15

    # Email Configuration
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "brevo")  # Options: brevo, resend, gmail, console
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@battle-d.com")

    # Brevo Configuration (recommended for Railway - no domain required)
    BREVO_API_KEY: Optional[str] = os.getenv("BREVO_API_KEY")
    BREVO_FROM_EMAIL: str = os.getenv("BREVO_FROM_EMAIL", "noreply@battle-d.com")
    BREVO_FROM_NAME: str = os.getenv("BREVO_FROM_NAME", "Battle-D")

    # Resend Configuration (requires domain verification)
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")

    # Gmail SMTP Configuration (blocked on Railway due to SMTP port restrictions)
    GMAIL_EMAIL: Optional[str] = os.getenv("GMAIL_EMAIL")
    GMAIL_APP_PASSWORD: Optional[str] = os.getenv("GMAIL_APP_PASSWORD")

    # Session
    SESSION_COOKIE_NAME: str = "battle_d_session"  # For authentication
    FLASH_SESSION_COOKIE_NAME: str = "flash_session"  # For flash messages
    SESSION_MAX_AGE_SECONDS: int = 86400 * 7  # 7 days

    # Backdoor Authentication (for emergency access when magic link fails)
    BACKDOOR_USERS: dict[str, str] = {
        "aissacasapro@gmail.com": "admin",
        "aissacasa.perso@gmail.com": "staff",
        "aissa.c@outlook.fr": "mc",
    }

    # Database
    @property
    def DATABASE_URL(self) -> str:
        """Get database URL with proper async driver.

        Ensures SQLite always uses aiosqlite async driver.
        Railway volume is mounted at /data, local dev uses ./data
        """
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            # Default for local development
            return "sqlite+aiosqlite:///./data/battle_d.db"

        # If URL is sqlite but doesn't have +aiosqlite, add it
        if db_url.startswith("sqlite://") and "+aiosqlite" not in db_url:
            db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        elif db_url.startswith("sqlite:") and "+aiosqlite" not in db_url:
            db_url = db_url.replace("sqlite:", "sqlite+aiosqlite:", 1)

        return db_url

    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"


settings = Settings()
