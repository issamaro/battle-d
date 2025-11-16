"""Gmail SMTP email provider implementation.

This module implements the EmailProvider interface using Gmail's SMTP server.
Requires Gmail account with App Password configured.
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.services.email.provider import BaseEmailProvider
from app.services.email.templates import (
    generate_magic_link_html,
    generate_magic_link_subject,
)


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
        # Validate email format
        if not self._validate_email(to_email):
            print(f"Invalid email format: {to_email}")
            return False

        try:
            # Create MIME message
            message = MIMEMultipart("alternative")
            message["From"] = self.gmail_email
            message["To"] = to_email
            message["Subject"] = generate_magic_link_subject()

            # Attach HTML body
            html_body = generate_magic_link_html(magic_link, first_name)
            message.attach(MIMEText(html_body, "html"))

            # Send via Gmail SMTP
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                use_tls=False,  # We'll use STARTTLS
            ) as smtp:
                await smtp.connect()
                await smtp.starttls()  # Upgrade to TLS
                await smtp.login(self.gmail_email, self.gmail_password)
                await smtp.send_message(message)

            print(f"Magic link email sent successfully to {to_email} via Gmail")
            return True

        except aiosmtplib.SMTPAuthenticationError as e:
            print(f"Gmail authentication failed: {e}")
            print(
                "Hint: Make sure you're using an App Password, not your regular password"
            )
            return False
        except aiosmtplib.SMTPException as e:
            print(f"SMTP error sending email via Gmail: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending email via Gmail: {e}")
            return False
