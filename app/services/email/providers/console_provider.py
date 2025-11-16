"""Console email provider implementation.

This module implements the EmailProvider interface by printing emails to console.
Used for development/testing when no actual email service is configured.
"""

import logging
from app.services.email.provider import BaseEmailProvider

logger = logging.getLogger(__name__)


class ConsoleEmailProvider(BaseEmailProvider):
    """Email provider that prints emails to console instead of sending them.

    Useful for local development and testing without requiring API keys.
    Preserves the original development mode behavior from the legacy implementation.

    This follows the Null Object Pattern - a valid provider that doesn't actually send emails.
    """

    def __init__(self):
        """Initialize console email provider.

        No configuration required since emails are printed to console.
        """
        pass

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Print magic link to console instead of sending email.

        Args:
            to_email: Recipient email address
            magic_link: The magic link URL for authentication
            first_name: Recipient's first name for personalization

        Returns:
            Always returns True since console printing cannot fail
        """
        logger.info(f"Console provider: Sending magic link to {to_email}")

        # Validate email format (even though we're not sending it)
        if not self._validate_email(to_email):
            logger.error(f"Invalid email format: {to_email}")
            return False

        # Print magic link to console (preserves original dev mode behavior)
        logger.info(f"\n{'='*60}")
        logger.info(f"MAGIC LINK for {first_name} ({to_email}):")
        logger.info(f"{magic_link}")
        logger.info(f"{'='*60}\n")

        return True
