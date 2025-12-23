"""E2E tests for delete confirmation modal button layout.

Tests BR-UI-001: Modal action buttons display side-by-side.
Tests BR-UX-001: No inline styles in templates.

Part of Phase 3.11 UX cleanup (deferred from Phase 3.10 UX Consistency Audit).
Updated for SCSS-based design system (Frontend Rebuild Phase 2).

Scenarios from feature-spec.md:
  - Buttons display side-by-side (Cancel left, Delete right)
  - No inline styles on buttons or form
  - Delete button uses class="btn btn-danger" (SCSS design system)
"""
import pytest
import re

from tests.e2e import assert_status_ok


class TestDeleteModalButtonLayout:
    """Tests for delete modal button layout (BR-UI-001, BR-UX-001)."""

    def test_delete_modal_has_modal_footer(self, admin_client):
        """Modal footer contains action buttons.

        Validates: feature-spec.md Scenario "Buttons display side-by-side"
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the delete modal contains a modal-footer wrapper
            And the buttons are inside the modal-footer
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)
        # Should contain modal-footer wrapper (SCSS design system)
        assert 'class="modal-footer"' in response.text

    def test_delete_modal_no_inline_styles_on_form(self, admin_client):
        """Modal form has no inline styles.

        Validates: feature-spec.md Scenario "No inline styles on buttons"
        Validates: BR-UX-001 No inline styles in production templates
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the delete modal form should not have style="" attribute
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)

        # Extract the delete modal form - look for form with delete action
        # Should NOT have style="display: inline;" pattern
        form_inline_pattern = r'<form[^>]*method="POST"[^>]*action="[^"]*delete[^"]*"[^>]*style='
        match = re.search(form_inline_pattern, response.text, re.IGNORECASE)
        assert match is None, "Delete form should not have inline styles"

    def test_delete_modal_no_inline_styles_on_buttons(self, admin_client):
        """Modal buttons have no inline background-color styles.

        Validates: feature-spec.md Scenario "Delete button uses design system class"
        Validates: BR-UX-001 No inline styles in production templates
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the delete button should not have style="background-color:..." attribute
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)

        # Should NOT have buttons with inline background-color styles
        # The old broken pattern: style="background-color: var(--pico-color-red-500);"
        button_inline_pattern = r'<button[^>]*style="[^"]*background-color[^"]*"'
        match = re.search(button_inline_pattern, response.text, re.IGNORECASE)
        assert match is None, "Buttons should not have inline background-color styles"

    def test_delete_modal_uses_btn_danger_class(self, admin_client):
        """Delete button uses class="btn btn-danger" per SCSS design system.

        Validates: feature-spec.md Scenario "Delete button uses design system class"
        Validates: FRONTEND.md §8 Delete Confirmation Modal pattern
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the delete button should have class="btn btn-danger"
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)

        # Within modal-footer, should have submit button with btn btn-danger class
        # Pattern: <button type="submit" class="btn btn-danger">
        assert 'class="btn btn-danger"' in response.text

    def test_delete_modal_cancel_button_type(self, admin_client):
        """Cancel button has type="button" to prevent form submission.

        Validates: feature-spec.md Scenario "Cancel button is clickable and inside form"
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the Cancel button should have type="button"
            And the Cancel button should have class="btn btn-secondary"
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)

        # Cancel button should be type="button" class="btn btn-secondary"
        # Pattern allows for attributes in different order
        cancel_pattern = r'<button[^>]*type="button"[^>]*class="btn btn-secondary"'
        match = re.search(cancel_pattern, response.text)
        assert match is not None, "Cancel button should have type='button' class='btn btn-secondary'"

    def test_delete_modal_buttons_inside_form(self, admin_client):
        """Both buttons are inside the same form element.

        Validates: feature-spec.md Scenario "Cancel button is clickable and inside form"
        Validates: FRONTEND.md §8 pattern - both buttons in single form
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then both Cancel and Delete buttons should be inside the form
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)

        # The structure should be:
        # <form ...>
        #   <button type="button" class="btn btn-secondary">Cancel</button>
        #   <button type="submit" class="btn btn-danger">Delete</button>
        # </form>

        # Check that modal-footer is inside form (not having a standalone cancel button before form)
        # Old broken pattern had: <button class="secondary">Cancel</button><form...>
        # New pattern has: <form><button...>

        # Look for the broken pattern (cancel button outside form)
        broken_pattern = r'<button[^>]*class="btn btn-secondary"[^>]*>[^<]*</button>\s*<form'
        broken_match = re.search(broken_pattern, response.text)
        assert broken_match is None, "Cancel button should not be outside the form"

        # Verify modal-footer is present (indicates new structure)
        assert 'modal-footer' in response.text


class TestDeleteModalWarningText:
    """Tests for delete modal warning text styling (BR-UX-001)."""

    def test_warning_text_no_inline_color(self, admin_client):
        """Warning text uses .modal-warning class, not inline color.

        Validates: BR-UX-001 No inline styles in production templates
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the modal-warning element should not have inline color style
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)

        # Old pattern: class="warning-text" ... style="color: var(--pico-color-red-500);"
        # New pattern: class="modal-warning" (no inline style)
        warning_inline_pattern = r'class="modal-warning"[^>]*style='
        match = re.search(warning_inline_pattern, response.text)
        assert match is None, "modal-warning should not have inline styles"

    def test_muted_text_uses_text_muted_class(self, admin_client):
        """Muted text uses text-muted class instead of inline styles.

        Validates: BR-UX-001 No inline styles in production templates
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then "This action cannot be undone" should use text-muted class
        """
        # Given (authenticated as admin via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)

        # New pattern: <p class="text-muted text-sm">This action cannot be undone.</p>
        assert "text-muted" in response.text
        assert "This action cannot be undone" in response.text
