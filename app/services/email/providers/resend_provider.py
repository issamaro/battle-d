"""Resend email provider implementation.

This module implements the EmailProvider interface using the official Resend Python SDK.
"""

import logging
import time
import resend
from app.services.email.provider import BaseEmailProvider
from app.services.email.templates import (
    generate_magic_link_html,
    generate_magic_link_subject,
)

logger = logging.getLogger(__name__)


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
        start_time = time.time()
        logger.info(f"Starting Resend email send to {to_email}")

        # Validate email format
        if not self._validate_email(to_email):
            logger.error(f"Invalid email format: {to_email}")
            return False

        try:
            # Prepare email parameters using Resend SDK format
            logger.debug(f"Preparing email parameters for {to_email}")
            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": generate_magic_link_subject(),
                "html": generate_magic_link_html(magic_link, first_name),
            }

            # Send email using Resend SDK
            logger.info(f"Calling Resend API to send email to {to_email}")
            email: resend.Email = resend.Emails.send(params)

            # Check if email was sent successfully
            # Resend SDK returns an Email object with an 'id' field on success
            if email and hasattr(email, "id"):
                elapsed = time.time() - start_time
                logger.info(f"Magic link email sent successfully to {to_email} (ID: {email.id}) in {elapsed:.2f}s")
                return True
            else:
                elapsed = time.time() - start_time
                logger.error(f"Failed to send magic link email to {to_email} after {elapsed:.2f}s")
                return False

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error after {elapsed:.2f}s sending email via Resend: {e}", exc_info=True)
            return False
