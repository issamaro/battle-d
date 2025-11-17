"""Email HTML templates.

This module contains all email template generation functions.
Separating templates from providers follows Single Responsibility Principle.

ARCHITECTURE: ONE Template Per Email Type
==========================================
All email providers (Brevo, Resend, Gmail, Console) use the SAME templates
from this module. This ensures consistency across providers and makes it easy
to update email designs in one place.

ADDING NEW EMAIL TYPES:
=======================
Follow this pattern for each new email type:

1. Create template functions in this file:
   - generate_<email_type>_html(...) -> str
   - generate_<email_type>_text(...) -> str  (optional plain text fallback)
   - generate_<email_type>_subject(...) -> str

2. Add method to EmailProvider interface (provider.py)

3. Implement in ALL 4 providers (brevo, resend, gmail, console)

4. Add facade method to EmailService (service.py)

Example for future tournament invitation email:

    def generate_tournament_invitation_html(
        tournament_name: str, dancer_name: str, registration_deadline: str
    ) -> str:
        '''Generate HTML for tournament invitation email.'''
        return f'''
        <!DOCTYPE html>
        <html>
        <body style="...">
            <h2>Hello {dancer_name},</h2>
            <p>You're invited to compete in {tournament_name}!</p>
            <p>Registration deadline: {registration_deadline}</p>
            ...
        </body>
        </html>
        '''

    def generate_tournament_invitation_subject(tournament_name: str) -> str:
        '''Generate subject for tournament invitation.'''
        return f"Invitation: {tournament_name} - Battle-D"
"""

from app.config import settings


def generate_magic_link_html(magic_link: str, first_name: str) -> str:
    """Generate HTML email content for magic link authentication.

    This template is used by ALL email providers (Brevo, Resend, Gmail).
    Features responsive design with inline CSS for maximum email client compatibility.

    Args:
        magic_link: Complete magic link URL
        first_name: User's first name for personalization

    Returns:
        HTML email content as string with inline styles
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Battle-D Login Link</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
        <h2 style="color: #2c3e50; margin-bottom: 20px;">Battle-D Login</h2>
        <p>Hello {first_name},</p>
        <p>Click the button below to log in to your Battle-D account:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{magic_link}"
               style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                Log In to Battle-D
            </a>
        </div>
        <p style="color: #7f8c8d; font-size: 14px;">
            This link will expire in {settings.MAGIC_LINK_EXPIRY_MINUTES} minutes for security reasons.
        </p>
        <p style="color: #7f8c8d; font-size: 14px;">
            If you didn't request this login link, you can safely ignore this email.
        </p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <p style="color: #95a5a6; font-size: 12px; text-align: center;">
            Battle-D Tournament Management System
        </p>
    </div>
</body>
</html>"""


def generate_magic_link_text(magic_link: str, first_name: str) -> str:
    """Generate plain text email content for magic link authentication.

    Plain text fallback for email clients that don't support HTML.
    Used by Brevo provider for maximum compatibility.

    Args:
        magic_link: Complete magic link URL
        first_name: User's first name for personalization

    Returns:
        Plain text email content as string
    """
    return f"""Battle-D Login

Hello {first_name},

Click the link below to log in to your Battle-D account:

{magic_link}

This link will expire in {settings.MAGIC_LINK_EXPIRY_MINUTES} minutes for security reasons.

If you didn't request this login link, you can safely ignore this email.

---
Battle-D Tournament Management System"""


def generate_magic_link_subject() -> str:
    """Generate subject line for magic link email.

    Returns:
        Email subject as string
    """
    return f"{settings.APP_NAME} - Login Link"
