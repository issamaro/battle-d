"""Email provider interface definition.

This module defines the abstract interface that all email providers must implement.
Following the Adapter Pattern and Dependency Inversion Principle (SOLID).
"""

from abc import ABC, abstractmethod
from typing import Protocol


class EmailProvider(Protocol):
    """Protocol defining the interface for email providers.

    Any email service (Resend, SendGrid, AWS SES, etc.) must implement this interface.
    This enables easy switching between providers without changing business logic.

    Example:
        class MyEmailProvider:
            async def send_magic_link(
                self, to_email: str, magic_link: str, first_name: str
            ) -> bool:
                # Implementation specific to provider
                pass
    """

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Send a magic link email for passwordless authentication.

        Args:
            to_email: Recipient email address
            magic_link: The magic link URL for authentication
            first_name: Recipient's first name for personalization

        Returns:
            True if email was sent successfully, False otherwise

        Raises:
            May raise provider-specific exceptions for critical failures
        """
        ...


class BaseEmailProvider(ABC):
    """Abstract base class for email providers with common functionality.

    Provides a concrete base implementation that can be extended by specific providers.
    Use this when you need shared behavior across multiple providers.
    """

    @abstractmethod
    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Send a magic link email for passwordless authentication.

        Args:
            to_email: Recipient email address
            magic_link: The magic link URL for authentication
            first_name: Recipient's first name for personalization

        Returns:
            True if email was sent successfully, False otherwise
        """
        pass

    def _validate_email(self, email: str) -> bool:
        """Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid, False otherwise
        """
        # Basic email validation
        return "@" in email and "." in email.split("@")[1]
