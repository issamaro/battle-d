"""Tests for Gmail SMTP email provider."""

import pytest
from app.services.email.providers.gmail_provider import GmailEmailProvider


class TestGmailProviderInitialization:
    """Test Gmail provider initialization and validation."""

    def test_valid_initialization(self):
        """Test successful initialization with valid credentials."""
        provider = GmailEmailProvider(
            gmail_email="test@gmail.com", gmail_password="abcd efgh ijkl mnop"
        )
        assert provider.gmail_email == "test@gmail.com"
        assert provider.gmail_password == "abcd efgh ijkl mnop"
        assert provider.smtp_server == "smtp.gmail.com"
        assert provider.smtp_port == 587

    def test_missing_email_raises_error(self):
        """Test initialization fails without email."""
        with pytest.raises(ValueError, match="Gmail email address is required"):
            GmailEmailProvider(gmail_email="", gmail_password="password123")

    def test_missing_password_raises_error(self):
        """Test initialization fails without password."""
        with pytest.raises(ValueError, match="Gmail App Password is required"):
            GmailEmailProvider(gmail_email="test@gmail.com", gmail_password="")

    def test_custom_smtp_settings(self):
        """Test initialization with custom SMTP server and port."""
        provider = GmailEmailProvider(
            gmail_email="test@gmail.com",
            gmail_password="password123",
            smtp_server="smtp.custom.com",
            smtp_port=465,
        )
        assert provider.smtp_server == "smtp.custom.com"
        assert provider.smtp_port == 465


class TestGmailProviderEmailValidation:
    """Test email validation in Gmail provider."""

    @pytest.mark.asyncio
    async def test_invalid_email_format(self):
        """Test that invalid email format returns False."""
        provider = GmailEmailProvider(
            gmail_email="sender@gmail.com", gmail_password="app-password"
        )

        result = await provider.send_magic_link(
            to_email="invalid-email",  # No @ symbol
            magic_link="https://example.com/verify?token=abc",
            first_name="Test",
        )

        assert result is False


# NOTE: We do NOT test actual SMTP sending in unit tests
# Integration tests with real Gmail would be:
# 1. Slow (network calls)
# 2. Unreliable (requires internet, Gmail availability)
# 3. Requires real credentials in CI/CD
#
# For real-world testing:
# - Use console provider in development
# - Manually test Gmail provider in staging
# - Use mock providers in automated tests
