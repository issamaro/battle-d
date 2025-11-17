"""Email provider interface definition.

This module defines the abstract interface that all email providers must implement.
Following the Adapter Pattern and Dependency Inversion Principle (SOLID).
"""

from abc import ABC, abstractmethod
from typing import Protocol


class EmailProvider(Protocol):
    """Protocol defining the interface for email providers.

    Any email service (Brevo, Resend, Gmail, etc.) must implement this interface.
    This enables easy switching between providers without changing business logic.

    ARCHITECTURE: Adapter Pattern
    ==============================
    All providers use the SAME templates from templates.py.
    Each provider only implements the sending logic specific to their API/SMTP.

    ADDING NEW EMAIL TYPES:
    =======================
    Follow this 4-step process (15-30 minutes per email type):

    Step 1: Add template functions to templates.py
        - generate_<email_type>_html(...) -> str
        - generate_<email_type>_text(...) -> str (optional)
        - generate_<email_type>_subject(...) -> str

    Step 2: Add method signature to this Protocol
        Example for tournament invitation:

        async def send_tournament_invitation(
            self, to_email: str, tournament_name: str, dancer_name: str
        ) -> bool:
            '''Send tournament invitation to dancer.

            Args:
                to_email: Dancer's email address
                tournament_name: Name of the tournament
                dancer_name: Dancer's first name for personalization

            Returns:
                True if email was sent successfully, False otherwise
            '''
            ...

    Step 3: Implement in ALL 4 providers (brevo, resend, gmail, console)
        Each provider imports the template and uses provider-specific sending:

        # In brevo_provider.py
        from app.services.email.templates import generate_tournament_invitation_html

        async def send_tournament_invitation(self, to_email, tournament_name, dancer_name):
            html = generate_tournament_invitation_html(tournament_name, dancer_name)
            # Use Brevo API to send html...
            return True

    Step 4: Add facade method to EmailService (service.py)
        async def send_tournament_invitation(self, ...):
            return await self.provider.send_tournament_invitation(...)

    Example Implementation:
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
