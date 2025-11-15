"""Authentication utilities for magic link authentication."""
from datetime import datetime, timedelta
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.config import settings


class MagicLinkAuth:
    """Handles magic link token generation and verification."""

    def __init__(self):
        self.serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

    def generate_token(self, email: str, role: str) -> str:
        """Generate a secure token for magic link authentication.

        Args:
            email: User email address
            role: User role (admin, staff, mc, judge)

        Returns:
            Secure token string
        """
        payload = {
            "email": email,
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
        }
        return self.serializer.dumps(payload, salt="magic-link")

    def verify_token(self, token: str, max_age: int = None) -> Optional[dict]:
        """Verify and decode a magic link token.

        Args:
            token: Token string to verify
            max_age: Maximum age in seconds (defaults to config setting)

        Returns:
            Payload dict with email and role, or None if invalid
        """
        if max_age is None:
            max_age = settings.MAGIC_LINK_EXPIRY_MINUTES * 60

        try:
            payload = self.serializer.loads(token, salt="magic-link", max_age=max_age)
            return payload
        except (SignatureExpired, BadSignature):
            return None

    def generate_magic_link(self, email: str, role: str) -> str:
        """Generate a complete magic link URL.

        Args:
            email: User email address
            role: User role

        Returns:
            Complete magic link URL
        """
        token = self.generate_token(email, role)
        return f"{settings.MAGIC_LINK_BASE_URL}/auth/verify?token={token}"


magic_link_auth = MagicLinkAuth()
