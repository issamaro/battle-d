"""Resend email provider implementation.

This module implements the EmailProvider interface using the official Resend Python SDK.
"""

import resend
from app.services.email.provider import BaseEmailProvider
from app.services.email.templates import (
    generate_magic_link_html,
    generate_magic_link_subject,
)


class ResendEmailProvider(BaseEmailProvider):
    """Email provider implementation using Resend API.

    Uses the official Resend Python SDK for sending emails.
    Requires RESEND_API_KEY to be configured.

    Attributes:
        api_key: Resend API key for authentication
        from_email: Default sender email address
    """

    def __init__(self, api_key: str, from_email: str):
        """Initialize Resend email provider.

        Args:
            api_key: Resend API key
            from_email: Default sender email address (must be verified in Resend)
        """
        if not api_key:
            raise ValueError("Resend API key is required")
        if not from_email:
            raise ValueError("From email address is required")

        self.api_key = api_key
        self.from_email = from_email

        # Configure Resend SDK
        resend.api_key = api_key

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Send magic link email using Resend API.

        Args:
            to_email: Recipient email address
            magic_link: The magic link URL for authentication
            first_name: Recipient's first name for personalization

        Returns:
            True if email was sent successfully, False otherwise
        """
        # Validate email format
        if not self._validate_email(to_email):
            print(f"Invalid email format: {to_email}")
            return False

        try:
            # Prepare email parameters using Resend SDK format
            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": generate_magic_link_subject(),
                "html": generate_magic_link_html(magic_link, first_name),
            }

            # Send email using Resend SDK
            email: resend.Email = resend.Emails.send(params)

            # Check if email was sent successfully
            # Resend SDK returns an Email object with an 'id' field on success
            if email and hasattr(email, "id"):
                print(f"Magic link email sent successfully to {to_email} (ID: {email.id})")
                return True
            else:
                print(f"Failed to send magic link email to {to_email}")
                return False

        except Exception as e:
            print(f"Error sending email via Resend: {e}")
            return False
