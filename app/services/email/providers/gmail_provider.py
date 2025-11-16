"""Gmail SMTP email provider implementation.

This module implements the EmailProvider interface using Gmail's SMTP server.
Requires Gmail account with App Password configured.
"""

import asyncio
import logging
import time
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.services.email.provider import BaseEmailProvider
from app.services.email.templates import (
    generate_magic_link_html,
    generate_magic_link_subject,
)

logger = logging.getLogger(__name__)


class GmailEmailProvider(BaseEmailProvider):
    """Email provider implementation using Gmail SMTP.

    Uses Gmail's SMTP server (smtp.gmail.com:587) with TLS encryption.
    Requires a Gmail account with App Password enabled (not regular password).

    Security Notes:
        - MUST use App Password, not account password
        - TLS encryption is enforced
        - Connection is established per-email (no persistent connection)

    Attributes:
        gmail_email: Gmail account email address (sender)
        gmail_password: Gmail App Password (16-character, no spaces)
        smtp_server: SMTP server address (default: smtp.gmail.com)
        smtp_port: SMTP port (default: 587 for TLS)
    """

    # Gmail SMTP configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587  # TLS port

    def __init__(
        self,
        gmail_email: str,
        gmail_password: str,
        smtp_server: str = SMTP_SERVER,
        smtp_port: int = SMTP_PORT,
    ):
        """Initialize Gmail SMTP provider.

        Args:
            gmail_email: Gmail account email (sender address)
            gmail_password: Gmail App Password (16 chars)
            smtp_server: SMTP server address (default: smtp.gmail.com)
            smtp_port: SMTP port (default: 587)

        Raises:
            ValueError: If gmail_email or gmail_password are empty
        """
        if not gmail_email:
            raise ValueError("Gmail email address is required")
        if not gmail_password:
            raise ValueError("Gmail App Password is required")

        self.gmail_email = gmail_email
        self.gmail_password = gmail_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Send magic link email via Gmail SMTP.

        Args:
            to_email: Recipient email address
            magic_link: The magic link URL for authentication
            first_name: Recipient's first name for personalization

        Returns:
            True if email was sent successfully, False otherwise
        """
        start_time = time.time()
        logger.info(f"Starting Gmail email send to {to_email}")

        # Validate email format
        if not self._validate_email(to_email):
            logger.error(f"Invalid email format: {to_email}")
            return False

        try:
            # Create MIME message
            logger.debug(f"Creating MIME message for {to_email}")
            message = MIMEMultipart("alternative")
            message["From"] = self.gmail_email
            message["To"] = to_email
            message["Subject"] = generate_magic_link_subject()

            # Attach HTML body
            html_body = generate_magic_link_html(magic_link, first_name)
            message.attach(MIMEText(html_body, "html"))

            # Send via Gmail SMTP with timeout
            logger.info(f"Connecting to Gmail SMTP server {self.smtp_server}:{self.smtp_port}")

            async with asyncio.timeout(15):  # 15 second total timeout
                async with aiosmtplib.SMTP(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    timeout=10,  # 10 second per-operation timeout
                    use_tls=False,  # We'll use STARTTLS
                ) as smtp:
                    logger.debug("Upgrading connection to TLS")
                    await smtp.starttls()  # Upgrade to TLS

                    logger.debug("Authenticating with Gmail")
                    await smtp.login(self.gmail_email, self.gmail_password)

                    logger.debug("Sending message")
                    await smtp.send_message(message)

            elapsed = time.time() - start_time
            logger.info(f"Magic link email sent successfully to {to_email} via Gmail in {elapsed:.2f}s")
            return True

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"Gmail SMTP timeout after {elapsed:.2f}s sending to {to_email}")
            logger.error("This usually indicates network issues or Gmail server unavailability")
            return False
        except aiosmtplib.SMTPAuthenticationError as e:
            elapsed = time.time() - start_time
            logger.error(f"Gmail authentication failed after {elapsed:.2f}s: {e}")
            logger.error("Hint: Make sure you're using an App Password, not your regular password")
            return False
        except aiosmtplib.SMTPException as e:
            elapsed = time.time() - start_time
            logger.error(f"SMTP error after {elapsed:.2f}s sending email via Gmail: {e}")
            return False
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Unexpected error after {elapsed:.2f}s sending email via Gmail: {e}", exc_info=True)
            return False
