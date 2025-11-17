"""Tests for email templates.

This module tests the centralized email template functions to ensure:
1. Templates contain all required elements
2. Templates handle personalization correctly
3. Templates are consistent across providers (architecture test)
"""

import pytest
from app.services.email.templates import (
    generate_magic_link_html,
    generate_magic_link_text,
    generate_magic_link_subject,
)


class TestMagicLinkTemplates:
    """Tests for magic link email templates."""

    def test_magic_link_html_contains_required_elements(self):
        """Test magic link HTML has all required elements."""
        magic_link = "https://example.com/verify?token=abc123"
        first_name = "John"

        html = generate_magic_link_html(magic_link, first_name)

        # Verify structure
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "<body" in html

        # Verify personalization
        assert "Hello John" in html

        # Verify magic link is present
        assert magic_link in html
        assert 'href="https://example.com/verify?token=abc123"' in html

        # Verify content
        assert "Battle-D Login" in html
        assert "Log In to Battle-D" in html
        assert "15 minutes" in html  # Expiration notice
        assert "Battle-D Tournament Management System" in html  # Footer

        # Verify security message
        assert "If you didn't request this login link" in html

    def test_magic_link_html_uses_styled_template(self):
        """Test that HTML uses the styled template (not simple version)."""
        html = generate_magic_link_html("https://example.com/verify", "Test")

        # Verify it's the styled version (has inline CSS)
        assert "background-color:" in html
        assert "font-family:" in html
        assert "style=" in html

        # Verify responsive design elements
        assert "max-width: 600px" in html

    def test_magic_link_text_contains_required_elements(self):
        """Test plain text fallback has all required elements."""
        magic_link = "https://example.com/verify?token=abc123"
        first_name = "Sarah"

        text = generate_magic_link_text(magic_link, first_name)

        # Verify it's plain text (no HTML tags)
        assert "<" not in text
        assert ">" not in text

        # Verify personalization
        assert "Hello Sarah" in text

        # Verify magic link
        assert magic_link in text

        # Verify content
        assert "Battle-D Login" in text
        assert "15 minutes" in text
        assert "Battle-D Tournament Management System" in text

    def test_magic_link_subject_format(self):
        """Test magic link subject line format."""
        subject = generate_magic_link_subject()

        assert "Battle-D" in subject
        assert "Login Link" in subject

        # Subject should be concise
        assert len(subject) < 50

    def test_magic_link_html_personalization_with_special_characters(self):
        """Test template handles names with special characters."""
        # Test with apostrophe
        html = generate_magic_link_html("https://example.com/verify", "O'Brien")
        assert "Hello O'Brien" in html

        # Test with hyphen
        html = generate_magic_link_html("https://example.com/verify", "Jean-Luc")
        assert "Hello Jean-Luc" in html

        # Test with accented characters
        html = generate_magic_link_html("https://example.com/verify", "José")
        assert "Hello José" in html

    def test_magic_link_with_complex_url(self):
        """Test template handles complex magic link URLs."""
        # URL with multiple query parameters
        complex_link = "https://battle-d.com/auth/verify?token=abc123&redirect=%2Fdashboard&foo=bar"
        html = generate_magic_link_html(complex_link, "Test")

        assert complex_link in html

    def test_all_templates_render_without_errors(self):
        """Ensure all template functions execute without errors."""
        # Magic link templates
        html = generate_magic_link_html("https://example.com/verify", "Test")
        assert html
        assert len(html) > 100

        text = generate_magic_link_text("https://example.com/verify", "Test")
        assert text
        assert len(text) > 50

        subject = generate_magic_link_subject()
        assert subject
        assert len(subject) > 5


class TestTemplateArchitecture:
    """Tests documenting and verifying the template architecture."""

    def test_one_template_per_email_type_architecture(self):
        """
        Document the architecture: ONE template per email type.

        This test verifies that all providers use the SAME template functions
        from templates.py, ensuring consistency across providers.
        """
        # Verify Brevo provider imports templates
        from app.services.email.providers.brevo_provider import (
            generate_magic_link_html,
            generate_magic_link_text,
            generate_magic_link_subject,
        )

        # Verify Resend provider imports templates
        from app.services.email.providers.resend_provider import (
            generate_magic_link_html as resend_html,
            generate_magic_link_subject as resend_subject,
        )

        # Verify Gmail provider imports templates
        from app.services.email.providers.gmail_provider import (
            generate_magic_link_html as gmail_html,
            generate_magic_link_subject as gmail_subject,
        )

        # All providers import from the SAME templates module
        # This ensures ONE template per email type, not one per provider
        from app.services.email.templates import (
            generate_magic_link_html as canonical_html,
            generate_magic_link_subject as canonical_subject,
        )

        # Verify they're the same functions
        assert generate_magic_link_html is canonical_html
        assert resend_html is canonical_html
        assert gmail_html is canonical_html

        assert generate_magic_link_subject is canonical_subject
        assert resend_subject is canonical_subject
        assert gmail_subject is canonical_subject

    def test_template_output_consistency(self):
        """
        Verify that the same inputs produce identical output.

        This ensures templates are deterministic and consistent.
        """
        magic_link = "https://example.com/verify?token=test"
        first_name = "TestUser"

        # Generate same template twice
        html1 = generate_magic_link_html(magic_link, first_name)
        html2 = generate_magic_link_html(magic_link, first_name)

        # Should be identical
        assert html1 == html2

        # Same for text
        text1 = generate_magic_link_text(magic_link, first_name)
        text2 = generate_magic_link_text(magic_link, first_name)
        assert text1 == text2


class TestFutureEmailTemplates:
    """Placeholder tests for future email types.

    When adding new email types, follow this pattern:

    1. Add template functions to app/services/email/templates.py:
       - generate_<email_type>_html(...)
       - generate_<email_type>_text(...) (optional)
       - generate_<email_type>_subject(...)

    2. Add test class here following the pattern above

    3. Add method to EmailProvider interface

    4. Implement in all 4 providers

    5. Add facade method to EmailService
    """

    def test_future_tournament_invitation_template_example(self):
        """
        Example test structure for future tournament invitation email.

        When implementing, uncomment and adapt this test:

        from app.services.email.templates import (
            generate_tournament_invitation_html,
            generate_tournament_invitation_subject,
        )

        html = generate_tournament_invitation_html(
            tournament_name="Battle of the Year 2024",
            dancer_name="Sarah",
            registration_deadline="2024-12-31"
        )

        assert "Sarah" in html
        assert "Battle of the Year 2024" in html
        assert "2024-12-31" in html
        assert "<!DOCTYPE html>" in html

        subject = generate_tournament_invitation_subject("Battle of the Year 2024")
        assert "Battle of the Year 2024" in subject
        assert "Invitation" in subject or "Invite" in subject
        """
        # Placeholder - implement when tournament invitations are added
        assert True
