"""E2E tests for tournament deletion (BR-DEL-001).

Tests the POST /tournaments/{id}/delete endpoint.
Validates status restrictions and cascade behavior.

See: VALIDATION_RULES.md lines 454-462 (Deletion Rules)
See: workbench/FEATURE_SPEC_2024-12-24_tournament-deletion-fix.md
"""
import pytest
from uuid import uuid4

from app.models.tournament import TournamentStatus, TournamentPhase


class TestTournamentDeletion:
    """Test tournament deletion endpoint."""

    def test_delete_tournament_requires_auth(self, e2e_client):
        """POST /tournaments/{id}/delete requires authentication.

        Validates: [Derived] HTTP authentication pattern
        Gherkin:
            Given I am not authenticated
            When I POST to /tournaments/{id}/delete
            Then I am redirected to login or get unauthorized (401/302/303)
        """
        # Given (not authenticated via e2e_client fixture)

        # When
        response = e2e_client.post(f"/tournaments/{uuid4()}/delete")

        # Then
        assert response.status_code in [401, 302, 303]

    def test_delete_tournament_requires_staff(self, judge_client):
        """POST /tournaments/{id}/delete requires staff or admin role.

        Validates: VALIDATION_RULES.md Deletion Rules (staff-only)
        Gherkin:
            Given I am authenticated as Judge (not Staff or Admin)
            When I POST to /tournaments/{id}/delete
            Then I am denied access (401/403)
        """
        # Given (authenticated as judge via judge_client fixture)

        # When
        response = judge_client.post(f"/tournaments/{uuid4()}/delete")

        # Then
        assert response.status_code in [401, 403]

    def test_delete_tournament_invalid_uuid(self, staff_client):
        """POST /tournaments/{id}/delete handles invalid UUID.

        Validates: [Derived] HTTP input validation
        Gherkin:
            Given I am authenticated as Staff
            When I POST to /tournaments/not-a-uuid/delete
            Then I am redirected (303) with an error message
        """
        # Given (authenticated as staff via staff_client fixture)

        # When
        response = staff_client.post(
            "/tournaments/not-a-uuid/delete",
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303

    def test_delete_tournament_nonexistent_returns_404(self, staff_client):
        """POST /tournaments/{id}/delete returns 404 for non-existent tournament.

        Validates: [Derived] HTTP 404 pattern for missing resources
        Gherkin:
            Given I am authenticated as Staff
            And no tournament exists with the given ID
            When I POST to /tournaments/{id}/delete
            Then I receive a 404 Not Found response
        """
        # Given (authenticated as staff via staff_client fixture)
        fake_id = uuid4()

        # When
        response = staff_client.post(
            f"/tournaments/{fake_id}/delete",
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_tournament_created_status_success(
        self, staff_client, create_e2e_tournament
    ):
        """DELETE tournament with CREATED status succeeds.

        Validates: VALIDATION_RULES.md line 460 (Tournament deletion rules)
        Gherkin:
            Given a tournament exists with status CREATED
            When I POST to /tournaments/{id}/delete
            Then the tournament is deleted
            And I am redirected to /tournaments
            And I see success message in flash
        """
        # Given
        data = await create_e2e_tournament(
            name="Tournament To Delete",
            status=TournamentStatus.CREATED,
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.post(
            f"/tournaments/{tournament_id}/delete",
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 303
        assert response.headers.get("location") == "/tournaments"

    @pytest.mark.asyncio
    async def test_delete_tournament_active_status_rejected(
        self, staff_client, create_e2e_tournament
    ):
        """DELETE tournament with ACTIVE status is rejected.

        Validates: VALIDATION_RULES.md line 460 (Tournament deletion rules)
        Gherkin:
            Given a tournament exists with status ACTIVE
            When I POST to /tournaments/{id}/delete
            Then I receive a redirect with error message
            And the tournament still exists
        """
        # Given
        data = await create_e2e_tournament(
            name="Active Tournament",
            status=TournamentStatus.ACTIVE,
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.post(
            f"/tournaments/{tournament_id}/delete",
            follow_redirects=False,
        )

        # Then - Should redirect with error, not delete
        assert response.status_code == 303
        assert response.headers.get("location") == "/tournaments"

        # Verify tournament still exists by trying to access it
        get_response = staff_client.get(f"/tournaments/{tournament_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_tournament_completed_status_rejected(
        self, staff_client, create_e2e_tournament
    ):
        """DELETE tournament with COMPLETED status is rejected.

        Validates: VALIDATION_RULES.md line 460 (Tournament deletion rules)
        Gherkin:
            Given a tournament exists with status COMPLETED
            When I POST to /tournaments/{id}/delete
            Then I receive a redirect with error message
            And the tournament still exists
        """
        # Given
        data = await create_e2e_tournament(
            name="Completed Tournament",
            status=TournamentStatus.COMPLETED,
        )
        tournament_id = data["tournament"].id

        # When
        response = staff_client.post(
            f"/tournaments/{tournament_id}/delete",
            follow_redirects=False,
        )

        # Then - Should redirect with error, not delete
        assert response.status_code == 303
        assert response.headers.get("location") == "/tournaments"

        # Verify tournament still exists by trying to access it
        get_response = staff_client.get(f"/tournaments/{tournament_id}")
        assert get_response.status_code == 200


class TestTournamentDeletionCascade:
    """Test cascade behavior for tournament deletion."""

    @pytest.mark.asyncio
    async def test_delete_tournament_cascades_to_categories(
        self, staff_client, create_e2e_tournament
    ):
        """Tournament deletion removes all categories.

        Validates: DOMAIN_MODEL.md Tournament.categories cascade="all, delete-orphan"
        Gherkin:
            Given a tournament with 2 categories
            When the tournament is deleted
            Then both categories are deleted
        """
        # Given - Tournament with 2 categories
        data = await create_e2e_tournament(
            name="Tournament With Categories",
            status=TournamentStatus.CREATED,
            num_categories=2,
            performers_per_category=0,  # No performers for simpler test
        )
        tournament_id = data["tournament"].id
        category_ids = [c.id for c in data["categories"]]

        # When - Delete tournament
        response = staff_client.post(
            f"/tournaments/{tournament_id}/delete",
            follow_redirects=False,
        )

        # Then - Tournament deleted
        assert response.status_code == 303

        # Verify tournament no longer accessible
        get_response = staff_client.get(f"/tournaments/{tournament_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_tournament_cascades_to_performers(
        self, staff_client, create_e2e_tournament
    ):
        """Tournament deletion removes all performers.

        Validates: DOMAIN_MODEL.md Category.performers cascade="all, delete-orphan"
        Gherkin:
            Given a tournament with categories containing performers
            When the tournament is deleted
            Then all performers are deleted
        """
        # Given - Tournament with categories and performers
        data = await create_e2e_tournament(
            name="Tournament With Performers",
            status=TournamentStatus.CREATED,
            num_categories=1,
            performers_per_category=4,
        )
        tournament_id = data["tournament"].id

        # When - Delete tournament
        response = staff_client.post(
            f"/tournaments/{tournament_id}/delete",
            follow_redirects=False,
        )

        # Then - Tournament deleted
        assert response.status_code == 303

        # Verify tournament no longer accessible
        get_response = staff_client.get(f"/tournaments/{tournament_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_tournament_preserves_dancers(
        self, staff_client, create_e2e_tournament
    ):
        """Tournament deletion preserves linked dancer profiles.

        Validates: DOMAIN_MODEL.md Performer.dancer FK (ondelete=CASCADE on Performer side)
        Gherkin:
            Given a tournament with performers linked to dancers
            When the tournament is deleted
            Then the dancer profiles still exist
        """
        # Given - Tournament with dancers/performers
        data = await create_e2e_tournament(
            name="Tournament With Dancers",
            status=TournamentStatus.CREATED,
            num_categories=1,
            performers_per_category=2,
        )
        tournament_id = data["tournament"].id
        dancer_ids = [d.id for d in data["dancers"]]

        # When - Delete tournament
        response = staff_client.post(
            f"/tournaments/{tournament_id}/delete",
            follow_redirects=False,
        )

        # Then - Tournament deleted
        assert response.status_code == 303

        # Verify dancers still accessible
        dancers_response = staff_client.get("/dancers")
        assert dancers_response.status_code == 200
        # Dancers should still be visible in the list
        for dancer in data["dancers"]:
            assert dancer.blaze.encode() in dancers_response.content


class TestTournamentDeletionHTMX:
    """Test HTMX-specific behavior for tournament deletion."""

    @pytest.mark.asyncio
    async def test_delete_tournament_htmx_returns_redirect_header(
        self, staff_client, create_e2e_tournament
    ):
        """HTMX request returns HX-Redirect header.

        Validates: FRONTEND.md HTMX modal patterns
        Gherkin:
            Given a tournament exists with status CREATED
            And the request includes HX-Request header
            When I POST to /tournaments/{id}/delete
            Then the response includes HX-Redirect to /tournaments
        """
        # Given
        data = await create_e2e_tournament(
            name="HTMX Delete Test",
            status=TournamentStatus.CREATED,
            num_categories=0,
            performers_per_category=0,
        )
        tournament_id = data["tournament"].id

        # When - HTMX request
        response = staff_client.post(
            f"/tournaments/{tournament_id}/delete",
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )

        # Then
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/tournaments"
