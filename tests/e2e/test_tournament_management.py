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
        """GET /tournaments/create loads tournament creation form.

        Validates: DOMAIN_MODEL.md Tournament entity creation
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /tournaments/create
            Then the page loads successfully (200)
            And I see a name input field
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/tournaments/create")

        # Then
        assert_status_ok(response)
        assert "name" in response.text.lower()

    def test_create_tournament_success(self, staff_client):
        """POST /tournaments/create creates tournament and redirects.

        Validates: DOMAIN_MODEL.md Tournament entity creation
        Gherkin:
            Given I am authenticated as Staff
            When I POST to /tournaments/create with valid tournament data
            Then I am redirected to the tournament detail page
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.post(
            "/tournaments/create",
            data={"name": "E2E Test Tournament"},
            follow_redirects=False,
        )

        # Then
        assert_redirect(response)
        assert "/tournaments/" in response.headers.get("location", "")

    def test_create_tournament_appears_in_list(self, staff_client):
        """Created tournament appears in tournament list.

        Validates: DOMAIN_MODEL.md Tournament entity access
        Gherkin:
            Given I am authenticated as Staff
            When I create a tournament named "List Test Tournament"
            And I navigate to /tournaments
            Then I see "List Test Tournament" in the list
        """
        # Given (authenticated via staff_client fixture)

        # When - Create
        staff_client.post(
            "/tournaments/create",
            data={"name": "List Test Tournament"},
        )

        # And - List
        response = staff_client.get("/tournaments")

        # Then
        assert_status_ok(response)
        assert "List Test Tournament" in response.text


class TestTournamentList:
    """Test tournament list page."""

    def test_tournament_list_loads(self, staff_client):
        """GET /tournaments loads tournament list page.

        Validates: DOMAIN_MODEL.md Tournament entity access
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /tournaments
            Then the page loads successfully (200)
        """
        # Given (authenticated via staff_client fixture)

        # When
        response = staff_client.get("/tournaments")

        # Then
        assert_status_ok(response)

    def test_tournament_list_requires_authentication(self, e2e_client):
        """GET /tournaments requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I navigate to /tournaments
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.get("/tournaments")

        # Then
        assert response.status_code in [401, 302, 303]


class TestTournamentDetail:
    """Test tournament detail page."""

    def test_tournament_detail_loads(self, staff_client, create_e2e_tournament):
        """GET /tournaments/{id} loads tournament detail page.

        Validates: DOMAIN_MODEL.md Tournament entity access
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists
            When I navigate to /tournaments/{id}
            Then the page loads successfully (200)
            And I see the tournament name
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        tournament = data["tournament"]

        # When
        response = staff_client.get(f"/tournaments/{tournament.id}")

        # Then
        assert_status_ok(response)
        assert tournament.name in response.text

    def test_tournament_detail_shows_categories(
        self, staff_client, create_e2e_tournament
    ):
        """GET /tournaments/{id} shows category information.

        Validates: DOMAIN_MODEL.md Category entity display
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists with 2 categories
            When I navigate to /tournaments/{id}
            Then the page loads successfully (200)
            And I see the category information
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=2)
        )
        tournament = data["tournament"]

        # When
        response = staff_client.get(f"/tournaments/{tournament.id}")

        # Then
        assert_status_ok(response)
        # Should show categories
        assert "Category" in response.text


class TestCategoryManagement:
    """Test adding categories to tournaments via HTTP."""

    def test_add_category_form_loads(self, staff_client, create_e2e_tournament):
        """GET /tournaments/{id}/add-category loads form.

        Validates: DOMAIN_MODEL.md Category entity creation
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists with no categories
            When I navigate to /tournaments/{id}/add-category
            Then the page loads successfully (200)
            And I see a name input field
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=0)
        )
        tournament = data["tournament"]

        # When
        response = staff_client.get(f"/tournaments/{tournament.id}/add-category")

        # Then
        assert_status_ok(response)
        assert "name" in response.text.lower()

    def test_add_category_to_tournament(self, staff_client, create_e2e_tournament):
        """POST /tournaments/{id}/add-category creates category.

        Validates: DOMAIN_MODEL.md Category entity creation
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists with no categories
            When I POST to /tournaments/{id}/add-category with category data
            Then I am redirected to the tournament detail page
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=0, performers_per_category=0)
        )
        tournament = data["tournament"]

        # When
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

        # Then
        assert_redirect(response)

    def test_category_appears_on_detail_page(self, staff_client, create_e2e_tournament):
        """Added category appears on tournament detail page.

        Validates: DOMAIN_MODEL.md Category entity display
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists
            When I add a category named "Visible Category"
            And I view the tournament detail page
            Then I see "Visible Category" on the page
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(num_categories=0, performers_per_category=0)
        )
        tournament = data["tournament"]

        # When - Add category
        staff_client.post(
            f"/tournaments/{tournament.id}/add-category",
            data={
                "name": "Visible Category",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
        )

        # And - View detail
        response = staff_client.get(f"/tournaments/{tournament.id}")

        # Then
        assert_status_ok(response)
        assert "Visible Category" in response.text


class TestPhaseOverview:
    """Test tournament phase overview page."""

    def test_phase_overview_loads(self, staff_client, create_e2e_tournament):
        """GET /tournaments/{id}/phase loads phase overview.

        Validates: DOMAIN_MODEL.md Tournament phase management
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists
            When I navigate to /tournaments/{id}/phase
            Then the page loads successfully (200)
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        tournament = data["tournament"]

        # When
        response = staff_client.get(f"/tournaments/{tournament.id}/phase")

        # Then
        assert_status_ok(response)

    def test_phase_overview_shows_current_phase(
        self, staff_client, create_e2e_tournament
    ):
        """GET /tournaments/{id}/phase shows current phase.

        Validates: DOMAIN_MODEL.md Tournament phase display
        Gherkin:
            Given I am authenticated as Staff
            And a tournament exists in REGISTRATION phase
            When I navigate to /tournaments/{id}/phase
            Then the page shows "registration" phase information
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament()
        )
        tournament = data["tournament"]

        # When
        response = staff_client.get(f"/tournaments/{tournament.id}/phase")

        # Then
        assert_status_ok(response)
        # Should show registration phase
        assert "registration" in response.text.lower()


class TestPhaseAdvancement:
    """Test advancing tournament phases via HTTP."""

    def test_advance_phase_requires_admin(self, staff_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance requires admin role.

        Validates: DOMAIN_MODEL.md User roles (admin-only phase advancement)
        Gherkin:
            Given I am authenticated as Staff (not Admin)
            And a tournament exists with sufficient performers
            When I POST to /tournaments/{id}/advance
            Then I am denied access (401/403)
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=4)
        )
        tournament = data["tournament"]

        # When
        response = staff_client.post(
            f"/tournaments/{tournament.id}/advance",
            follow_redirects=False,
        )

        # Then
        # Staff cannot advance phases (admin only)
        assert response.status_code in [401, 403]

    def test_advance_phase_shows_validation(self, admin_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance with insufficient performers shows errors.

        Validates: VALIDATION_RULES.md Phase Transition Validation
        Gherkin:
            Given I am authenticated as Admin
            And a tournament exists with only 1 performer per category
            When I POST to /tournaments/{id}/advance without confirmation
            Then I see validation errors or a confirmation page
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=1)
        )
        tournament = data["tournament"]

        # When
        response = admin_client.post(
            f"/tournaments/{tournament.id}/advance",
            data={"confirmed": "false"},
        )

        # Then
        # Should show validation errors or confirmation page
        # Status could be 200 (error page) or 400 (validation failed)
        assert response.status_code in [200, 400]

    def test_advance_phase_shows_confirmation(self, admin_client, create_e2e_tournament):
        """POST /tournaments/{id}/advance shows confirmation page.

        Validates: VALIDATION_RULES.md Phase Transition Validation
        Gherkin:
            Given I am authenticated as Admin
            And a tournament exists with sufficient performers (5 per category)
            When I POST to /tournaments/{id}/advance without confirmation
            Then I see a confirmation or validation page (200)
        """
        # Given
        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(performers_per_category=5)  # Enough for advancement
        )
        tournament = data["tournament"]

        # When
        response = admin_client.post(
            f"/tournaments/{tournament.id}/advance",
            data={"confirmed": "false"},
        )

        # Then
        # Should show confirmation or validation page
        assert_status_ok(response)
