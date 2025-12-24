"""E2E tests for Category Creation Phase Validation (BR-CAT-001).

Tests that categories can only be created when tournament status is CREATED.
See: FEATURE_SPEC_2025-12-24_CATEGORY-CREATION-PHASE-VALIDATION.md
"""
import pytest
import pytest_asyncio

from app.models.tournament import TournamentPhase, TournamentStatus
from tests.e2e import (
    assert_status_ok,
    assert_redirect,
    assert_contains_text,
)


class TestCategoryCreationStatusValidation:
    """Test BR-CAT-001: Category creation status restriction."""

    def test_create_category_allowed_when_created(
        self, staff_client, create_e2e_tournament
    ):
        """Category creation succeeds when tournament status is CREATED.

        Validates: VALIDATION_RULES.md BR-CAT-001
        Gherkin:
            Given a tournament with status "CREATED"
            And the tournament is in "REGISTRATION" phase
            When I submit the add category form
            Then the category should be created successfully
            And I should see a success message
        """
        # Given - create tournament via fixture
        import asyncio

        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(
                name="Category Test CREATED",
                status=TournamentStatus.CREATED,
                phase=TournamentPhase.REGISTRATION,
                num_categories=0,
                performers_per_category=0,
            )
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Test Category",
                "is_duo": False,
                "groups_ideal": 2,
                "performers_ideal": 4,
            },
            follow_redirects=True,
        )

        # Then
        assert_status_ok(response)
        assert "Test Category" in response.text

    def test_create_category_blocked_when_active(
        self, staff_client, create_e2e_tournament
    ):
        """Category creation fails when tournament status is ACTIVE.

        Validates: VALIDATION_RULES.md BR-CAT-001
        Gherkin:
            Given a tournament with status "ACTIVE"
            And the tournament is in "PRESELECTION" phase
            When I submit the add category form
            Then the category should NOT be created
            And I should see an error message "Categories can only be added when tournament is in CREATED status"
        """
        # Given
        import asyncio

        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(
                name="Category Test ACTIVE",
                status=TournamentStatus.ACTIVE,
                phase=TournamentPhase.PRESELECTION,
                num_categories=1,
                performers_per_category=5,
            )
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Blocked Category",
                "is_duo": False,
                "groups_ideal": 2,
                "performers_ideal": 4,
            },
            follow_redirects=True,
        )

        # Then
        assert_status_ok(response)
        assert "Categories can only be added when tournament is in CREATED status" in response.text
        assert "Blocked Category" not in response.text

    def test_create_category_blocked_when_completed(
        self, staff_client, create_e2e_tournament
    ):
        """Category creation fails when tournament status is COMPLETED.

        Validates: VALIDATION_RULES.md BR-CAT-001
        Gherkin:
            Given a tournament with status "COMPLETED"
            When I submit the add category form
            Then the category should NOT be created
            And I should see an error message "Categories can only be added when tournament is in CREATED status"
        """
        # Given
        import asyncio

        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(
                name="Category Test COMPLETED",
                status=TournamentStatus.COMPLETED,
                phase=TournamentPhase.COMPLETED,
                num_categories=1,
                performers_per_category=5,
            )
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Blocked Category",
                "is_duo": False,
                "groups_ideal": 2,
                "performers_ideal": 4,
            },
            follow_redirects=True,
        )

        # Then
        assert_status_ok(response)
        assert "Categories can only be added when tournament is in CREATED status" in response.text
        assert "Blocked Category" not in response.text

    def test_add_category_form_blocked_when_active(
        self, staff_client, create_e2e_tournament
    ):
        """Add category form redirects when tournament is ACTIVE.

        Validates: VALIDATION_RULES.md BR-CAT-001
        Gherkin:
            Given a tournament with status "ACTIVE"
            When I navigate to the add category form
            Then I should be redirected to the tournament detail page
            And I should see an error message
        """
        # Given
        import asyncio

        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(
                name="Form Test ACTIVE",
                status=TournamentStatus.ACTIVE,
                phase=TournamentPhase.PRESELECTION,
                num_categories=1,
                performers_per_category=5,
            )
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.get(
            f"/tournaments/{tournament_id}/add-category",
            follow_redirects=True,
        )

        # Then
        assert_status_ok(response)
        assert "Categories can only be added when tournament is in CREATED status" in response.text

    def test_add_category_button_hidden_when_active(
        self, staff_client, create_e2e_tournament
    ):
        """Add Category button not shown for ACTIVE tournaments.

        Validates: VALIDATION_RULES.md BR-CAT-001
        Gherkin:
            Given a tournament with status "ACTIVE"
            When I navigate to the tournament detail page
            Then the "Add Category" button should not be visible
        """
        # Given
        import asyncio

        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(
                name="Button Test ACTIVE",
                status=TournamentStatus.ACTIVE,
                phase=TournamentPhase.PRESELECTION,
                num_categories=1,
                performers_per_category=5,
            )
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.get(f"/tournaments/{tournament_id}")

        # Then
        assert_status_ok(response)
        assert "Button Test ACTIVE" in response.text
        # The "Add Category" link should NOT be present
        assert f"/tournaments/{tournament_id}/add-category" not in response.text

    def test_add_category_button_visible_when_created(
        self, staff_client, create_e2e_tournament
    ):
        """Add Category button shown for CREATED tournaments.

        Validates: VALIDATION_RULES.md BR-CAT-001
        Gherkin:
            Given a tournament with status "CREATED"
            When I navigate to the tournament detail page
            Then the "Add Category" button should be visible
        """
        # Given
        import asyncio

        data = asyncio.get_event_loop().run_until_complete(
            create_e2e_tournament(
                name="Button Test CREATED",
                status=TournamentStatus.CREATED,
                phase=TournamentPhase.REGISTRATION,
                num_categories=0,
                performers_per_category=0,
            )
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.get(f"/tournaments/{tournament_id}")

        # Then
        assert_status_ok(response)
        assert "Button Test CREATED" in response.text
        # The "Add Category" link SHOULD be present
        assert f"/tournaments/{tournament_id}/add-category" in response.text
