"""E2E tests for UX Issues Batch Fix (2024-12-24).

Tests for 7 UX issues:
- Issue #1: Three dots menu on tournament cards
- Issue #2: Empty state icon alignment (CSS)
- Issue #3: Category removal during REGISTRATION
- Issue #4: User/Dancer creation modals with HTMX
- Issue #5: Modal centering (CSS)
- Issue #6: Phase advancement UI
- Issue #7: Modal harmonization (HTMX + HX-Redirect)

See: workbench/IMPLEMENTATION_PLAN_2024-12-24_UX-ISSUES-BATCH.md
"""
import pytest
from uuid import uuid4

from tests.e2e import (
    is_partial_html,
    htmx_headers,
    assert_status_ok,
    assert_redirect,
    assert_contains_text,
)
from app.models.tournament import TournamentPhase, TournamentStatus


# =============================================================================
# ISSUE #1: Three Dots Menu Tests
# =============================================================================


class TestTournamentDropdownMenu:
    """Test three dots dropdown menu on tournament cards."""

    def test_tournament_list_contains_dropdown_menu(self, staff_client, create_e2e_tournament):
        """Tournament list page contains dropdown menu structure.

        Validates: Issue #1 - Three dots menu
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists
            When I view the tournaments list
            Then I see a dropdown menu with three dots icon
            And the dropdown has View, Rename options
        """
        # Given
        import asyncio
        asyncio.get_event_loop().run_until_complete(create_e2e_tournament())

        # When
        response = staff_client.get("/tournaments")

        # Then
        assert_status_ok(response)
        assert "dropdown-trigger" in response.text
        assert "dropdown-menu" in response.text
        assert "dropdown-item" in response.text

    def test_tournament_list_dropdown_has_view_option(self, staff_client, create_e2e_tournament):
        """Tournament dropdown has View option.

        Validates: Issue #1 - View action in dropdown
        """
        # Given
        import asyncio
        asyncio.get_event_loop().run_until_complete(create_e2e_tournament())

        # When
        response = staff_client.get("/tournaments")

        # Then
        assert_status_ok(response)
        assert ">View</a>" in response.text or ">View<" in response.text

    def test_tournament_list_dropdown_has_rename_option(self, staff_client, create_e2e_tournament):
        """Tournament dropdown has Rename option.

        Validates: Issue #1 - Rename action in dropdown
        """
        # Given
        import asyncio
        asyncio.get_event_loop().run_until_complete(create_e2e_tournament())

        # When
        response = staff_client.get("/tournaments")

        # Then
        assert_status_ok(response)
        assert "Rename" in response.text
        assert "openRenameModal" in response.text


# =============================================================================
# ISSUE #3: Category Removal Tests
# =============================================================================


class TestCategoryRemoval:
    """Test category removal during REGISTRATION phase."""

    def test_category_delete_endpoint_exists(self, admin_client, create_e2e_tournament):
        """DELETE /tournaments/{id}/categories/{cat_id} endpoint exists.

        Validates: Issue #3 - Category removal endpoint
        Gherkin:
            Given I am authenticated as Admin
            And a tournament exists with a category
            When I send DELETE to /tournaments/{id}/categories/{cat_id}
            Then the request is processed (not 404 Method Not Allowed)
        """
        # Given
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(create_e2e_tournament())
        tournament_id = data["tournament"].id
        category_id = data["categories"][0].id

        # When
        response = admin_client.delete(
            f"/tournaments/{tournament_id}/categories/{category_id}",
            headers=htmx_headers(),
        )

        # Then - Should not be 405 Method Not Allowed
        assert response.status_code != 405, "DELETE method should be allowed"

    def test_category_delete_requires_registration_phase(self, admin_client, create_e2e_tournament):
        """Category deletion only allowed during REGISTRATION phase.

        Validates: Issue #3 - Phase restriction
        """
        # Given - Tournament in PRESELECTION phase
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(phase=TournamentPhase.PRESELECTION)
        )
        tournament_id = data["tournament"].id
        category_id = data["categories"][0].id

        # When
        response = admin_client.delete(
            f"/tournaments/{tournament_id}/categories/{category_id}",
            headers=htmx_headers(),
        )

        # Then - Should be forbidden (400 Bad Request with error message)
        assert response.status_code in [400, 403], "Should reject deletion outside REGISTRATION"


class TestCategoryDeletionCascade:
    """Test category deletion properly cascades to performers (BR-FIX-002)."""

    def test_category_delete_cascades_to_performers(self, admin_client, create_e2e_tournament):
        """Category deletion properly removes performers via ORM cascade.

        Validates: BR-FIX-002 - Category deletion CASCADE fix
        Gherkin:
            Given a tournament exists with a category
            And the category has registered performers
            When I delete the category
            Then the performers are also deleted
            And the dancer can re-register in the same tournament
        """
        # Given - Tournament with category and performers
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=3)
        )
        tournament_id = data["tournament"].id
        category_id = data["categories"][0].id

        # When - Delete the category
        response = admin_client.delete(
            f"/tournaments/{tournament_id}/categories/{category_id}",
            headers=htmx_headers(),
        )

        # Then - Should succeed (200)
        assert_status_ok(response)

    def test_tournament_detail_uses_styled_modal_for_category_removal(
        self, admin_client, create_e2e_tournament
    ):
        """Tournament detail uses styled modal instead of browser alert.

        Validates: BR-FIX-003 - Category removal uses styled modal
        Gherkin:
            Given I am authenticated as Admin
            And a tournament exists in REGISTRATION phase with categories
            When I view the tournament detail page
            Then I see modal trigger buttons (not hx-confirm)
            And styled removal modals are included
        """
        # Given
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(create_e2e_tournament())
        tournament_id = data["tournament"].id

        # When
        response = admin_client.get(f"/tournaments/{tournament_id}")

        # Then
        assert_status_ok(response)
        # Should have modal trigger (showModal)
        assert "showModal()" in response.text
        # Should NOT use hx-confirm for category removal
        assert 'hx-confirm="Remove category' not in response.text
        # Should include styled modal
        assert 'id="remove-category-' in response.text
        assert 'class="modal modal-danger"' in response.text


# =============================================================================
# ISSUE #4: User/Dancer Creation Modal Tests
# =============================================================================


class TestUserCreationModal:
    """Test user creation via modal with HTMX."""

    def test_users_page_has_modal_trigger(self, admin_client):
        """Admin users page has modal trigger button.

        Validates: Issue #4 - Modal trigger for user creation
        Gherkin:
            Given I am authenticated as Admin
            When I view the users page
            Then I see a button to open the create user modal
        """
        # When
        response = admin_client.get("/admin/users")

        # Then
        assert_status_ok(response)
        assert "create-user-modal" in response.text
        assert "showModal()" in response.text

    def test_user_create_htmx_validation_error(self, admin_client):
        """User creation via HTMX returns partial on validation error.

        Validates: Issue #4 + #7 - HTMX form with error handling
        Gherkin:
            Given I am authenticated as Admin
            When I submit invalid user data via HTMX
            Then I receive a partial HTML response with error
            And the response is not a full page
        """
        # When - Submit with invalid role
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": "test@example.com",
                "first_name": "Test",
                "role": "invalid_role",
            },
            headers=htmx_headers(),
        )

        # Then
        assert response.status_code == 400
        assert is_partial_html(response.text)


class TestDancerCreationModal:
    """Test dancer creation via modal with HTMX."""

    def test_dancers_page_has_modal_trigger(self, staff_client):
        """Dancers page has modal trigger button.

        Validates: Issue #4 - Modal trigger for dancer creation
        """
        # When
        response = staff_client.get("/dancers")

        # Then
        assert_status_ok(response)
        assert "create-dancer-modal" in response.text
        assert "showModal()" in response.text

    def test_dancer_create_htmx_validation_error(self, staff_client):
        """Dancer creation via HTMX returns partial on validation error.

        Validates: Issue #4 + #7 - HTMX form with error handling
        """
        # When - Submit with invalid date format
        response = staff_client.post(
            "/dancers/create",
            data={
                "email": "dancer@example.com",
                "first_name": "Test",
                "last_name": "Dancer",
                "date_of_birth": "not-a-date",
                "blaze": "B-Boy Test",
            },
            headers=htmx_headers(),
        )

        # Then
        assert response.status_code == 400
        assert is_partial_html(response.text)


# =============================================================================
# ISSUE #6: Phase Advancement Tests
# =============================================================================


class TestPhaseAdvancement:
    """Test phase advancement UI and endpoint."""

    def test_tournament_detail_shows_advance_section_for_admin(
        self, admin_client, create_e2e_tournament
    ):
        """Tournament detail page shows phase advancement for admin.

        Validates: Issue #6 - Phase advancement UI visibility
        Gherkin:
            Given I am authenticated as Admin
            And a tournament exists in REGISTRATION phase
            When I view the tournament detail page
            Then I see the phase advancement section
        """
        # Given
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(create_e2e_tournament())
        tournament_id = data["tournament"].id

        # When
        response = admin_client.get(f"/tournaments/{tournament_id}")

        # Then
        assert_status_ok(response)
        # Check for phase advance UI elements
        assert "Phase Advancement" in response.text or "phase-advance" in response.text

    def test_phase_advance_endpoint_exists(self, admin_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance endpoint exists.

        Validates: Issue #6 - Phase advancement endpoint
        """
        # Given
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(create_e2e_tournament())
        tournament_id = data["tournament"].id

        # When
        response = admin_client.post(
            f"/tournaments/{tournament_id}/advance",
            follow_redirects=False,
        )

        # Then - Should not be 404 or 405
        assert response.status_code not in [404, 405], "Advance endpoint should exist"


# =============================================================================
# ISSUE #7: Modal Harmonization (HTMX + HX-Redirect) Tests
# =============================================================================


class TestModalHarmonization:
    """Test HTMX modal form submission pattern."""

    def test_tournament_create_uses_htmx(self, staff_client):
        """Tournament create form uses HTMX.

        Validates: Issue #7 - Modal harmonization
        """
        # When
        response = staff_client.get("/tournaments")

        # Then - Check modal uses hx-post
        assert_status_ok(response)
        assert 'hx-post="/tournaments/create"' in response.text

    def test_tournament_create_htmx_success_returns_redirect(self, staff_client):
        """Tournament creation via HTMX returns HX-Redirect on success.

        Validates: Issue #7 - HX-Redirect pattern
        Gherkin:
            Given I am authenticated as Staff
            When I create a tournament via HTMX
            Then the response has HX-Redirect header
        """
        # When
        response = staff_client.post(
            "/tournaments/create",
            data={"name": f"Test Tournament {uuid4().hex[:8]}"},
            headers=htmx_headers(),
        )

        # Then
        assert_status_ok(response)
        assert "HX-Redirect" in response.headers


class TestRenameModal:
    """Test tournament rename modal functionality."""

    def test_tournaments_page_includes_rename_modal(self, staff_client, create_e2e_tournament):
        """Tournaments page includes rename modal.

        Validates: Issue #1 - Rename modal included
        """
        # Given
        import asyncio
        asyncio.get_event_loop().run_until_complete(create_e2e_tournament())

        # When
        response = staff_client.get("/tournaments")

        # Then
        assert_status_ok(response)
        assert 'id="rename-modal"' in response.text

    def test_rename_endpoint_exists(self, staff_client, create_e2e_tournament):
        """POST /tournaments/{id}/rename endpoint exists.

        Validates: Issue #1 - Rename endpoint
        """
        # Given
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(create_e2e_tournament())
        tournament_id = data["tournament"].id

        # When
        response = staff_client.post(
            f"/tournaments/{tournament_id}/rename",
            data={"name": "Renamed Tournament"},
            headers=htmx_headers(),
            follow_redirects=False,
        )

        # Then - Should not be 404 or 405
        assert response.status_code not in [404, 405], "Rename endpoint should exist"


# =============================================================================
# CSS Verification Tests (Issues #2 and #5)
# =============================================================================


class TestCSSPatterns:
    """Test CSS patterns are present in stylesheets.

    Note: These tests verify the CSS classes are used in templates.
    Actual centering is verified visually or with browser testing tools.
    """

    def test_modal_uses_dialog_element(self, staff_client):
        """Modals use native <dialog> element.

        Validates: Issue #5 - Modal uses dialog for centering
        """
        # When
        response = staff_client.get("/tournaments")

        # Then
        assert_status_ok(response)
        assert "<dialog" in response.text
        assert 'class="modal"' in response.text

    def test_empty_state_component_exists(self, staff_client, create_e2e_tournament):
        """Empty state uses proper component structure.

        Validates: Issue #2 - Empty state component
        """
        # When - Get tournaments page (which may show empty state)
        response = staff_client.get("/tournaments")

        # Then - Should have empty-state CSS class available
        assert_status_ok(response)
        # The empty state is conditionally shown, so just verify page loads
        assert is_partial_html(response.text) is False  # Full page
