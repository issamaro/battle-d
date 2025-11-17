"""Brevo (Sendinblue) email provider implementation."""

import logging
from typing import Optional
import brevo_python
from brevo_python.rest import ApiException

from app.services.email.provider import BaseEmailProvider
from app.services.email.templates import (
    generate_magic_link_html,
    generate_magic_link_text,
    generate_magic_link_subject,
)

logger = logging.getLogger(__name__)


class BrevoEmailProvider(BaseEmailProvider):
    """Email provider using Brevo (Sendinblue) API.

    Works on Railway without domain verification.
    Free tier: 300 emails/day.
    Uses HTTPS API (not SMTP), so works on platforms that block SMTP ports.

    Required environment variables:
    - BREVO_API_KEY: API key from Brevo dashboard
    - BREVO_FROM_EMAIL: Sender email address (e.g., noreply@battle-d.com)
    - BREVO_FROM_NAME: Sender name (e.g., Battle-D)
    """

    def __init__(
        self,
        api_key: str,
        from_email: str,
        from_name: str = "Battle-D",
    ):
        """Initialize Brevo email provider.

        Args:
            api_key: Brevo API key
            from_email: Sender email address
            from_name: Sender name
        """
        if not api_key:
            raise ValueError("Brevo API key is required")
        if not from_email:
            raise ValueError("From email is required")

        self.from_email = from_email
        self.from_name = self._truncate_name(from_name)

        # Configure Brevo API client
        configuration = brevo_python.Configuration()
        configuration.api_key["api-key"] = api_key
        self.api_instance = brevo_python.TransactionalEmailsApi(
            brevo_python.ApiClient(configuration)
        )

        logger.info(
            f"Brevo email provider initialized with from_email={from_email}, from_name={from_name}"
        )

    @staticmethod
    def _truncate_name(name: str, max_length: int = 70) -> str:
        """Truncate name to maximum allowed length per Brevo SDK requirements.

        Args:
            name: Name to truncate
            max_length: Maximum allowed characters (default: 70 per SDK docs)

        Returns:
            Truncated name if longer than max_length, otherwise original name
        """
        if len(name) > max_length:
            logger.warning(
                f"Name '{name}' exceeds {max_length} chars, truncating to '{name[:max_length]}'"
            )
            return name[:max_length]
        return name

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Send magic link email using Brevo API.

        Args:
            to_email: Recipient email address
            magic_link: Magic link URL for authentication
            first_name: Recipient's first name

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending magic link via Brevo to {to_email}")

            # Create email sender
            sender = brevo_python.SendSmtpEmailSender(
                name=self.from_name, email=self.from_email
            )

            # Create email recipient (truncate name per SDK requirements)
            to = [brevo_python.SendSmtpEmailTo(
                email=to_email,
                name=self._truncate_name(first_name)
            )]

            # Generate email content from centralized templates
            # All providers use the SAME templates for consistency
            html_content = generate_magic_link_html(magic_link, first_name)
            text_content = generate_magic_link_text(magic_link, first_name)
            subject = generate_magic_link_subject()

            # Create email object with tags for analytics
            send_smtp_email = brevo_python.SendSmtpEmail(
                sender=sender,
                to=to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                tags=["magic-link", "authentication"],
            )

            # Send email via Brevo API
            api_response = self.api_instance.send_transac_email(send_smtp_email)

            # Validate response
            if api_response and hasattr(api_response, 'message_id') and api_response.message_id:
                logger.info(
                    f"Brevo email sent successfully to {to_email}, message_id={api_response.message_id}"
                )
                return True
            else:
                logger.error(
                    f"Brevo API returned invalid response for {to_email}: {api_response}"
                )
                return False

        except ApiException as e:
            logger.error(
                f"Brevo API error sending to {to_email}: status={e.status}, reason={e.reason}, body={e.body}"
            )
            return False

        except Exception as e:
            logger.error(
                f"Unexpected error sending Brevo email to {to_email}: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return False
