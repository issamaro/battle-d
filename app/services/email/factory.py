"""Email provider factory.

This module provides a factory function to create the appropriate email provider
based on application configuration. Follows the Factory Pattern for provider selection.
"""

from typing import Optional
from app.config import settings
from app.services.email.provider import EmailProvider
from app.services.email.providers.console_provider import ConsoleEmailProvider
from app.services.email.providers.resend_provider import ResendEmailProvider
from app.services.email.providers.gmail_provider import GmailEmailProvider


def create_email_provider() -> EmailProvider:
    """Create and configure the appropriate email provider based on settings.

    This factory function determines which email provider to instantiate based on:
    1. EMAIL_PROVIDER setting (explicit provider selection)
    2. RESEND_API_KEY availability (fallback to console if not set)

    Returns:
        Configured EmailProvider instance (ResendEmailProvider, GmailEmailProvider, or ConsoleEmailProvider)

    Raises:
        ValueError: If provider configuration is invalid

    Example:
        >>> provider = create_email_provider()
        >>> await provider.send_magic_link("user@example.com", "https://...", "John")
    """
    # Get provider type from settings (default to "resend")
    provider_type = getattr(settings, "EMAIL_PROVIDER", "resend").lower()

    # Console provider (development mode)
    if provider_type == "console":
        print("Using console email provider (development mode)")
        return ConsoleEmailProvider()

    # Resend provider (production mode)
    if provider_type == "resend":
        api_key: Optional[str] = settings.RESEND_API_KEY
        from_email: str = settings.FROM_EMAIL

        # Fallback to console if API key not configured
        if not api_key:
            print(
                "RESEND_API_KEY not configured. Falling back to console email provider."
            )
            return ConsoleEmailProvider()

        print(f"Using Resend email provider (from: {from_email})")
        return ResendEmailProvider(api_key=api_key, from_email=from_email)

    # Gmail provider (production mode with personal Gmail)
    if provider_type == "gmail":
        gmail_email: Optional[str] = settings.GMAIL_EMAIL
        gmail_password: Optional[str] = settings.GMAIL_APP_PASSWORD

        # Fallback to console if credentials not configured
        if not gmail_email or not gmail_password:
            print(
                "GMAIL_EMAIL or GMAIL_APP_PASSWORD not configured. "
                "Falling back to console email provider."
            )
            return ConsoleEmailProvider()

        print(f"Using Gmail SMTP email provider (from: {gmail_email})")
        return GmailEmailProvider(
            gmail_email=gmail_email, gmail_password=gmail_password
        )

    # Future providers can be added here:
    # if provider_type == "sendgrid":
    #     return SendGridEmailProvider(...)
    # if provider_type == "ses":
    #     return AWSEmailProvider(...)

    # Invalid provider type
    raise ValueError(
        f"Unknown email provider: {provider_type}. "
        f"Supported providers: resend, gmail, console"
    )
