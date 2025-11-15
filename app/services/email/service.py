"""Email service for Battle-D application.

This module provides the main EmailService class that uses dependency injection
to work with any email provider implementation. Follows SOLID principles:
- Single Responsibility: Only coordinates email sending
- Dependency Inversion: Depends on EmailProvider interface, not concrete implementations
- Open/Closed: Open for extension (new providers) but closed for modification
"""

from app.services.email.provider import EmailProvider


class EmailService:
    """High-level email service that delegates to configured provider.

    This service acts as a facade, providing a simple interface for the application
    while delegating the actual email sending to the injected provider.

    Attributes:
        provider: The email provider implementation to use for sending emails

    Example:
        >>> from app.services.email.factory import create_email_provider
        >>> provider = create_email_provider()
        >>> email_service = EmailService(provider)
        >>> await email_service.send_magic_link("user@example.com", "https://...", "John")
    """

    def __init__(self, provider: EmailProvider):
        """Initialize email service with a specific provider.

        Args:
            provider: EmailProvider implementation (ResendEmailProvider, ConsoleEmailProvider, etc.)

        Example:
            >>> from app.services.email.providers import ResendEmailProvider
            >>> provider = ResendEmailProvider(api_key="...", from_email="...")
            >>> service = EmailService(provider)
        """
        self.provider = provider

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Send magic link email using the configured provider.

        This method delegates to the provider's send_magic_link implementation.
        The provider could be Resend, Console, or any future email service.

        Args:
            to_email: Recipient email address
            magic_link: Complete magic link URL for authentication
            first_name: User's first name for email personalization

        Returns:
            True if email was sent successfully, False otherwise

        Example:
            >>> success = await email_service.send_magic_link(
            ...     "user@example.com",
            ...     "https://battle-d.com/auth/verify?token=...",
            ...     "John"
            ... )
        """
        return await self.provider.send_magic_link(to_email, magic_link, first_name)
