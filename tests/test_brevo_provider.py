"""Tests for Brevo email provider."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.email.providers.brevo_provider import BrevoEmailProvider
import brevo_python
from brevo_python.rest import ApiException


class TestBrevoEmailProvider:
    """Tests for BrevoEmailProvider."""

    def test_init_requires_api_key(self):
        """Test that initialization fails without API key."""
        with pytest.raises(ValueError, match="Brevo API key is required"):
            BrevoEmailProvider(api_key="", from_email="test@example.com")

    def test_init_requires_from_email(self):
        """Test that initialization fails without from_email."""
        with pytest.raises(ValueError, match="From email is required"):
            BrevoEmailProvider(api_key="test-key", from_email="")

    def test_init_success(self):
        """Test successful initialization."""
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
            from_name="Battle-D",
        )

        assert provider.from_email == "noreply@battle-d.com"
        assert provider.from_name == "Battle-D"
        assert provider.api_instance is not None

    @pytest.mark.asyncio
    async def test_send_magic_link_success(self):
        """Test successful magic link email sending."""
        # Create provider
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
            from_name="Battle-D",
        )

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.message_id = "test-message-id-12345"

        with patch.object(
            provider.api_instance, "send_transac_email", return_value=mock_response
        ) as mock_send:
            # Send email
            result = await provider.send_magic_link(
                to_email="user@example.com",
                magic_link="https://battle-d.com/auth/verify?token=abc123",
                first_name="John",
            )

            # Verify result
            assert result is True

            # Verify API was called
            assert mock_send.call_count == 1
            call_args = mock_send.call_args[0][0]

            # Verify email structure
            assert isinstance(call_args, brevo_python.SendSmtpEmail)
            assert call_args.sender.email == "noreply@battle-d.com"
            assert call_args.sender.name == "Battle-D"
            assert len(call_args.to) == 1
            assert call_args.to[0].email == "user@example.com"
            assert call_args.to[0].name == "John"
            assert call_args.subject == "Battle-D - Login Link"  # Uses centralized template

            # Verify magic link is in content
            assert "https://battle-d.com/auth/verify?token=abc123" in call_args.html_content
            assert "https://battle-d.com/auth/verify?token=abc123" in call_args.text_content
            assert "John" in call_args.html_content

    @pytest.mark.asyncio
    async def test_send_magic_link_api_error(self):
        """Test handling of Brevo API error."""
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
        )

        # Mock API exception
        api_exception = ApiException(status=401, reason="Unauthorized")
        api_exception.body = '{"message": "Invalid API key"}'

        with patch.object(
            provider.api_instance, "send_transac_email", side_effect=api_exception
        ):
            result = await provider.send_magic_link(
                to_email="user@example.com",
                magic_link="https://battle-d.com/auth/verify?token=abc123",
                first_name="John",
            )

            # Should return False on error
            assert result is False

    @pytest.mark.asyncio
    async def test_send_magic_link_unexpected_error(self):
        """Test handling of unexpected error."""
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
        )

        # Mock unexpected exception
        with patch.object(
            provider.api_instance,
            "send_transac_email",
            side_effect=Exception("Network error"),
        ):
            result = await provider.send_magic_link(
                to_email="user@example.com",
                magic_link="https://battle-d.com/auth/verify?token=abc123",
                first_name="John",
            )

            # Should return False on error
            assert result is False

    @pytest.mark.asyncio
    async def test_email_content_structure(self):
        """Test that email content has proper structure."""
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
            from_name="Test Sender",
        )

        mock_response = MagicMock()
        mock_response.message_id = "test-id"

        with patch.object(
            provider.api_instance, "send_transac_email", return_value=mock_response
        ) as mock_send:
            await provider.send_magic_link(
                to_email="user@test.com",
                magic_link="https://example.com/verify?token=xyz",
                first_name="Alice",
            )

            call_args = mock_send.call_args[0][0]

            # Check HTML content has key elements
            html_content = call_args.html_content
            assert "<!DOCTYPE html>" in html_content
            assert "Alice" in html_content
            assert "https://example.com/verify?token=xyz" in html_content
            assert "Battle-D" in html_content
            assert "15 minutes" in html_content  # Expiry message

            # Check text content has key elements
            text_content = call_args.text_content
            assert "Alice" in text_content
            assert "https://example.com/verify?token=xyz" in text_content
            assert "Battle-D" in text_content
            assert "15 minutes" in text_content

    @pytest.mark.asyncio
    async def test_name_truncation(self):
        """Test that long names are truncated to 70 characters."""
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
            from_name="Test Sender",
        )

        # Create a name longer than 70 characters
        long_name = "A" * 80
        expected_truncated = "A" * 70

        mock_response = MagicMock()
        mock_response.message_id = "test-id"

        with patch.object(
            provider.api_instance, "send_transac_email", return_value=mock_response
        ) as mock_send:
            result = await provider.send_magic_link(
                to_email="user@test.com",
                magic_link="https://example.com/verify?token=xyz",
                first_name=long_name,
            )

            assert result is True

            # Verify recipient name was truncated
            call_args = mock_send.call_args[0][0]
            assert len(call_args.to[0].name) == 70
            assert call_args.to[0].name == expected_truncated

    @pytest.mark.asyncio
    async def test_sender_name_truncation(self):
        """Test that long sender names are truncated during initialization."""
        long_sender_name = "B" * 80
        expected_truncated = "B" * 70

        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
            from_name=long_sender_name,
        )

        # Verify sender name was truncated
        assert len(provider.from_name) == 70
        assert provider.from_name == expected_truncated

    @pytest.mark.asyncio
    async def test_email_tags_included(self):
        """Test that emails include analytics tags."""
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
            from_name="Test Sender",
        )

        mock_response = MagicMock()
        mock_response.message_id = "test-id"

        with patch.object(
            provider.api_instance, "send_transac_email", return_value=mock_response
        ) as mock_send:
            result = await provider.send_magic_link(
                to_email="user@test.com",
                magic_link="https://example.com/verify?token=xyz",
                first_name="Alice",
            )

            assert result is True

            # Verify tags are included
            call_args = mock_send.call_args[0][0]
            assert hasattr(call_args, 'tags')
            assert call_args.tags == ["magic-link", "authentication"]

    @pytest.mark.asyncio
    async def test_invalid_response_validation(self):
        """Test that invalid API responses are handled properly."""
        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
        )

        # Mock response without message_id
        mock_response = MagicMock()
        mock_response.message_id = None

        with patch.object(
            provider.api_instance, "send_transac_email", return_value=mock_response
        ):
            result = await provider.send_magic_link(
                to_email="user@test.com",
                magic_link="https://example.com/verify?token=xyz",
                first_name="Test",
            )

            # Should return False when response is invalid
            assert result is False

    @pytest.mark.asyncio
    async def test_uses_centralized_templates(self):
        """Test that Brevo provider uses centralized templates from templates.py.

        This verifies the architecture: ONE template per email type, shared across
        ALL providers (Brevo, Resend, Gmail, Console).
        """
        from app.services.email.templates import (
            generate_magic_link_html,
            generate_magic_link_text,
            generate_magic_link_subject,
        )

        provider = BrevoEmailProvider(
            api_key="test-api-key",
            from_email="noreply@battle-d.com",
            from_name="Battle-D",
        )

        mock_response = MagicMock()
        mock_response.message_id = "test-id"

        magic_link = "https://battle-d.com/verify?token=test123"
        first_name = "TestUser"

        with patch.object(
            provider.api_instance, "send_transac_email", return_value=mock_response
        ) as mock_send:
            result = await provider.send_magic_link(
                to_email="user@test.com",
                magic_link=magic_link,
                first_name=first_name,
            )

            assert result is True

            # Get the email that was sent
            call_args = mock_send.call_args[0][0]

            # Verify HTML content matches centralized template
            expected_html = generate_magic_link_html(magic_link, first_name)
            assert call_args.html_content == expected_html

            # Verify text content matches centralized template
            expected_text = generate_magic_link_text(magic_link, first_name)
            assert call_args.text_content == expected_text

            # Verify subject matches centralized template
            expected_subject = generate_magic_link_subject()
            assert call_args.subject == expected_subject

            # Verify it's using the styled template (not simple version)
            assert "<!DOCTYPE html>" in call_args.html_content
            assert "background-color:" in call_args.html_content  # Has inline CSS
            assert "Battle-D Login" in call_args.html_content
