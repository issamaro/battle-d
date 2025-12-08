"""E2E tests for Tournament Management (Admin/Staff workflow).

Tests tournament setup through HTTP interface.
See: FEATURE_SPEC_2025-12-08_E2E-TESTING-FRAMEWORK.md §3.2
"""
import pytest
import asyncio

from app.models.tournament import TournamentPhase
from tests.e2e import (
    assert_status_ok,
    assert_redirect,
    assert_contains_text,
)


class TestTournamentCreation:
    """Test creating tournaments via HTTP."""

    def test_create_tournament_form_loads(self, staff_client):
        """GET /tournaments/create loads tournament creation form."""
        response = staff_client.get("/tournaments/create")

        assert_status_ok(response)
        assert "name" in response.text.lower()

    def test_create_tournament_success(self, staff_client):
        """POST /tournaments/create creates tournament and redirects."""
        response = staff_client.post(
            "/tournaments/create",
            data={"name": "E2E Test Tournament"},
            follow_redirects=False,
        )

        assert_redirect(response)
        assert "/tournaments/" in response.headers.get("location", "")

    def test_create_tournament_appears_in_list(self, staff_client):
        """Created tournament appears in tournament list."""
        # Create
        staff_client.post(
            "/tournaments/create",
            data={"name": "List Test Tournament"},
        )

        # List
        response = staff_client.get("/tournaments")

        assert_status_ok(response)
        assert "List Test Tournament" in response.text


class TestTournamentList:
    """Test tournament list page."""

    def test_tournament_list_loads(self, staff_client):
        """GET /tournaments loads tournament list page."""
        response = staff_client.get("/tournaments")

        assert_status_ok(response)

    def test_tournament_list_requires_authentication(self, e2e_client):
        """GET /tournaments requires authentication."""
        response = e2e_client.get("/tournaments")

        assert response.status_code in [401, 302, 303]


class TestTournamentDetail:
    """Test tournament detail page."""

    def test_tournament_detail_loads(self, staff_client, create_e2e_tournament):
        """GET /tournaments/{id} loads tournament detail page."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        tournament = data["tournament"]

        response = staff_client.get(f"/tournaments/{tournament.id}")

        assert_status_ok(response)
        assert tournament.name in response.text

    def test_tournament_detail_shows_categories(
        self, staff_client, create_e2e_tournament
    ):
        """GET /tournaments/{id} shows category information."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=2)
        )
        tournament = data["tournament"]

        response = staff_client.get(f"/tournaments/{tournament.id}")

        assert_status_ok(response)
        # Should show categories
        assert "Category" in response.text


class TestCategoryManagement:
    """Test adding categories to tournaments via HTTP."""

    def test_add_category_form_loads(self, staff_client, create_e2e_tournament):
        """GET /tournaments/{id}/add-category loads form."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=0)
        )
        tournament = data["tournament"]

        response = staff_client.get(f"/tournaments/{tournament.id}/add-category")

        assert_status_ok(response)
        assert "name" in response.text.lower()

    def test_add_category_to_tournament(self, staff_client, create_e2e_tournament):
        """POST /tournaments/{id}/add-category creates category."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=0, performers_per_category=0)
        )
        tournament = data["tournament"]

        response = staff_client.post(
            f"/tournaments/{tournament.id}/add-category",
            data={
                "name": "New Category",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            follow_redirects=False,
        )

        assert_redirect(response)

    def test_category_appears_on_detail_page(self, staff_client, create_e2e_tournament):
        """Added category appears on tournament detail page."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=0, performers_per_category=0)
        )
        tournament = data["tournament"]

        # Add category
        staff_client.post(
            f"/tournaments/{tournament.id}/add-category",
            data={
                "name": "Visible Category",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
        )

        # View detail
        response = staff_client.get(f"/tournaments/{tournament.id}")

        assert_status_ok(response)
        assert "Visible Category" in response.text


class TestPhaseOverview:
    """Test tournament phase overview page."""

    def test_phase_overview_loads(self, staff_client, create_e2e_tournament):
        """GET /tournaments/{id}/phase loads phase overview."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        tournament = data["tournament"]

        response = staff_client.get(f"/tournaments/{tournament.id}/phase")

        assert_status_ok(response)

    def test_phase_overview_shows_current_phase(
        self, staff_client, create_e2e_tournament
    ):
        """GET /tournaments/{id}/phase shows current phase."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        tournament = data["tournament"]

        response = staff_client.get(f"/tournaments/{tournament.id}/phase")

        assert_status_ok(response)
        # Should show registration phase
        assert "registration" in response.text.lower()


class TestPhaseAdvancement:
    """Test advancing tournament phases via HTTP."""

    def test_advance_phase_requires_admin(self, staff_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance requires admin role."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=4)
        )
        tournament = data["tournament"]

        response = staff_client.post(
            f"/tournaments/{tournament.id}/advance",
            follow_redirects=False,
        )

        # Staff cannot advance phases (admin only)
        assert response.status_code in [401, 403]

    def test_advance_phase_shows_validation(self, admin_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance with insufficient performers shows errors."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=1)
        )
        tournament = data["tournament"]

        response = admin_client.post(
            f"/tournaments/{tournament.id}/advance",
            data={"confirmed": "false"},
        )

        # Should show validation errors or confirmation page
        # Status could be 200 (error page) or 400 (validation failed)
        assert response.status_code in [200, 400]

    def test_advance_phase_shows_confirmation(self, admin_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance shows confirmation page."""
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=5)  # Enough for advancement
        )
        tournament = data["tournament"]

        response = admin_client.post(
            f"/tournaments/{tournament.id}/advance",
            data={"confirmed": "false"},
        )

        # Should show confirmation or validation page
        assert_status_ok(response)
