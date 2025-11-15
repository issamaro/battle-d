"""Email service for sending magic links."""
from typing import Optional
import httpx
from app.config import settings


class EmailService:
    """Handles sending emails via Resend API."""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.FROM_EMAIL
        self.base_url = "https://api.resend.com"

    async def send_magic_link(self, to_email: str, magic_link: str, first_name: str) -> bool:
        """Send magic link email to user.

        Args:
            to_email: Recipient email address
            magic_link: Complete magic link URL
            first_name: User's first name for personalization

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.api_key:
            # Development mode: print link to console
            print(f"\n{'='*60}")
            print(f"MAGIC LINK for {first_name} ({to_email}):")
            print(f"{magic_link}")
            print(f"{'='*60}\n")
            return True

        # Production: send via Resend
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.from_email,
                        "to": [to_email],
                        "subject": f"{settings.APP_NAME} - Login Link",
                        "html": self._generate_email_html(magic_link, first_name),
                    },
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def _generate_email_html(self, magic_link: str, first_name: str) -> str:
        """Generate HTML email content.

        Args:
            magic_link: Complete magic link URL
            first_name: User's first name

        Returns:
            HTML email content
        """
        return f"""
        <html>
            <body>
                <h2>Hello {first_name},</h2>
                <p>Click the link below to log in to {settings.APP_NAME}:</p>
                <p><a href="{magic_link}">Login to {settings.APP_NAME}</a></p>
                <p>This link will expire in {settings.MAGIC_LINK_EXPIRY_MINUTES} minutes.</p>
                <p>If you didn't request this login link, please ignore this email.</p>
            </body>
        </html>
        """


email_service = EmailService()
