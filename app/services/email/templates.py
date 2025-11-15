"""Email HTML templates.

This module contains all email template generation functions.
Separating templates from providers follows Single Responsibility Principle.
"""

from app.config import settings


def generate_magic_link_html(magic_link: str, first_name: str) -> str:
    """Generate HTML email content for magic link authentication.

    Args:
        magic_link: Complete magic link URL
        first_name: User's first name for personalization

    Returns:
        HTML email content as string
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


def generate_magic_link_subject() -> str:
    """Generate subject line for magic link email.

    Returns:
        Email subject as string
    """
    return f"{settings.APP_NAME} - Login Link"
