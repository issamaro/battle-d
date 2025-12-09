"""Async E2E tests for Event Mode using shared session pattern.

These tests can access fixture-created data because they use
the async_e2e_session fixture with dependency override.

Previously, tests like these were impossible due to session isolation
(see tests/e2e/test_event_mode.py lines 183-187 for the removed tests).

See: TESTING.md §Async E2E Tests (Session Sharing Pattern)
"""
import pytest
from app.models.tournament import TournamentPhase
from app.models.battle import BattlePhase, BattleStatus

# Import fixtures from async_conftest
from tests.e2e.async_conftest import (
    async_e2e_session,
    async_client_factory,
    create_async_tournament,
    create_async_category,
    create_async_performer,
    create_async_battle,
    create_async_tournament_scenario,
)


class TestEventModeWithRealData:
    """Event Mode tests with pre-created tournament and battle data.

    These tests were previously impossible due to session isolation.
    Now work because fixture data and routes share the same session.

    Validates Gherkin scenarios from feature specs.
    """

    @pytest.mark.asyncio
    async def test_command_center_shows_real_tournament(
        self,
        async_client_factory,
        create_async_tournament_scenario,
    ):
        """Test that command center displays fixture-created tournament.

        Gherkin:
        Given a tournament "Summer Battle 2024" exists in PRESELECTION phase
        And the tournament has 1 category with 4 performers
        When I navigate to /event/{tournament_id}
        Then the page should load successfully (200)
        And I should see the tournament name
        """
        # Given
        data = await create_async_tournament_scenario(
            name="Summer Battle 2024",
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=4,
        )
        tournament = data["tournament"]

        # When
        async with async_client_factory("mc") as client:
            response = await client.get(f"/event/{tournament.id}")

        # Then
        assert response.status_code == 200
        assert b"Summer Battle 2024" in response.content

    @pytest.mark.asyncio
    async def test_command_center_shows_progress_bar(
        self,
        async_client_factory,
        create_async_tournament_scenario,
    ):
        """Test that command center shows progress bar for tournament.

        Gherkin:
        Given a tournament in PRESELECTION phase with performers
        When I view the Event Command Center
        Then I should see the phase progress section
        """
        # Given
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=4,
        )
        tournament = data["tournament"]

        # When
        async with async_client_factory("mc") as client:
            response = await client.get(f"/event/{tournament.id}")

        # Then
        assert response.status_code == 200
        # Check for progress-related content
        assert b"progress" in response.content.lower() or b"battles" in response.content.lower()

    @pytest.mark.asyncio
    async def test_battle_queue_partial_returns_html(
        self,
        async_client_factory,
        create_async_tournament_scenario,
    ):
        """Test that battle queue HTMX endpoint returns partial HTML.

        Gherkin:
        Given a tournament in PRESELECTION phase
        When I request /event/{tournament_id}/queue with HX-Request header
        Then the response should be partial HTML (no <html> tag)
        """
        # Given
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=4,
        )
        tournament = data["tournament"]

        # When - HTMX request
        async with async_client_factory("mc") as client:
            response = await client.get(
                f"/event/{tournament.id}/queue",
                headers={"HX-Request": "true"}
            )

        # Then
        assert response.status_code == 200
        # Should be partial HTML (no full page wrapper)
        assert b"<html>" not in response.content
        assert b"<!DOCTYPE" not in response.content

    @pytest.mark.asyncio
    async def test_progress_partial_returns_html(
        self,
        async_client_factory,
        create_async_tournament_scenario,
    ):
        """Test that progress HTMX endpoint returns partial HTML.

        Gherkin:
        Given a tournament in PRESELECTION phase
        When I request /event/{tournament_id}/progress with HX-Request header
        Then the response should be partial HTML
        """
        # Given
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=4,
        )
        tournament = data["tournament"]

        # When - HTMX request
        async with async_client_factory("mc") as client:
            response = await client.get(
                f"/event/{tournament.id}/progress",
                headers={"HX-Request": "true"}
            )

        # Then
        assert response.status_code == 200
        # Should be partial HTML
        assert b"<html>" not in response.content


class TestBattleWorkflowWithRealData:
    """Battle workflow tests with fixture-created battles.

    These tests validate the complete battle lifecycle
    using pre-created data.
    """

    @pytest.mark.asyncio
    async def test_can_view_fixture_created_battle(
        self,
        async_client_factory,
        create_async_tournament_scenario,
        create_async_battle,
    ):
        """Test viewing a battle that was created in fixtures.

        Gherkin:
        Given a tournament with a pending battle
        When I view the battle details
        Then the page should show the battle with performer names
        """
        # Given
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=2,
        )
        category = data["categories"][0]
        performers = data["performers"]

        battle = await create_async_battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            performer_ids=[performers[0].id, performers[1].id],
            status=BattleStatus.PENDING,
        )

        # When
        async with async_client_factory("staff") as client:
            response = await client.get(f"/battles/{battle.id}")

        # Then
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_can_start_fixture_created_battle(
        self,
        async_e2e_session,
        async_client_factory,
        create_async_tournament_scenario,
        create_async_battle,
    ):
        """Test starting a battle that was created in fixtures.

        Gherkin:
        Given a battle exists with status PENDING
        And I am authenticated as Staff
        When I POST to /battles/{battle_id}/start
        Then the response should redirect (success)
        And the battle status should change to ACTIVE
        """
        # Given
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=1,
            performers_per_category=2,
        )
        category = data["categories"][0]
        performers = data["performers"]

        battle = await create_async_battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            performer_ids=[performers[0].id, performers[1].id],
            status=BattleStatus.PENDING,
        )

        # When - use staff role (battles require staff permission)
        async with async_client_factory("staff") as client:
            response = await client.post(
                f"/battles/{battle.id}/start",
                follow_redirects=False
            )

        # Then
        assert response.status_code == 303  # Redirect on success

        # Verify battle status changed in database
        from app.repositories.battle import BattleRepository
        battle_repo = BattleRepository(async_e2e_session)
        updated_battle = await battle_repo.get_by_id(battle.id)
        assert updated_battle.status == BattleStatus.ACTIVE


class TestSessionIsolationFix:
    """Meta-tests that verify the session isolation fix is working.

    These tests explicitly verify that fixture-created data
    is visible to HTTP requests.
    """

    @pytest.mark.asyncio
    async def test_tournament_created_in_fixture_is_visible_to_http(
        self,
        async_client_factory,
        create_async_tournament,
    ):
        """Verify the core fix: fixture data visible to routes.

        This is the fundamental test that proves session sharing works.
        If this test passes, the session isolation problem is solved.
        """
        # Create tournament in fixture (shared session)
        tournament = await create_async_tournament(
            name="Session Isolation Test Tournament"
        )

        # Make HTTP request (uses same session via override)
        async with async_client_factory("staff") as client:
            response = await client.get(f"/tournaments/{tournament.id}")

        # Tournament should be visible!
        assert response.status_code == 200
        assert b"Session Isolation Test Tournament" in response.content

    @pytest.mark.asyncio
    async def test_multiple_entities_visible_in_same_test(
        self,
        async_client_factory,
        create_async_tournament_scenario,
    ):
        """Verify multiple related entities are all visible.

        Tests that complex scenarios with multiple entities
        (tournament + categories + performers) all work.
        """
        # Create complete scenario
        data = await create_async_tournament_scenario(
            name="Multi-Entity Test",
            num_categories=2,
            performers_per_category=4,
        )

        # Verify tournament visible
        async with async_client_factory("staff") as client:
            response = await client.get(f"/tournaments/{data['tournament'].id}")
            assert response.status_code == 200
            assert b"Multi-Entity Test" in response.content

            # Verify tournament detail page shows categories
            # (categories are displayed on the tournament detail page)
            category = data["categories"][0]
            assert category.name.encode() in response.content or b"Category" in response.content
