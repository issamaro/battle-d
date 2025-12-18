"""Tests for phases routes consolidation.

Validates that old phase routes are removed and phase management is
consolidated into Event Mode.
See: FEATURE_SPEC_2024-12-18_SCREEN-CONSOLIDATION.md
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def unauthenticated_client():
    """Create test client without authentication."""
    return TestClient(app)


class TestPhasesRoutesRemoved:
    """Tests that old phases routes are removed.

    Phase management has been consolidated into Event Mode.
    The old /tournaments/{id}/phase and /tournaments/{id}/advance routes
    have been replaced by /event/{id}/advance.
    """

    def test_phases_prefix_route_does_not_exist(self, unauthenticated_client):
        """Route /phases/{id}/phase should NOT exist."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/phases/{fake_id}/phase")

        # This route should NOT exist
        assert response.status_code == 404

    def test_phases_advance_route_does_not_exist(self, unauthenticated_client):
        """Route /phases/advance should NOT exist."""
        response = unauthenticated_client.post("/phases/advance")

        # This route should NOT exist
        assert response.status_code == 404

    def test_phases_go_back_route_does_not_exist(self, unauthenticated_client):
        """Route /phases/go-back should NOT exist."""
        response = unauthenticated_client.post("/phases/go-back")

        # This route should NOT exist (we removed it)
        assert response.status_code == 404


class TestOldPhasesRoutesRemoved:
    """Tests that the consolidated routes are removed.

    These routes existed under /tournaments/{id}/ but have been
    consolidated into Event Mode (/event/{id}/).
    """

    def test_phases_overview_removed(self, unauthenticated_client):
        """GET /tournaments/{id}/phase returns 404 (route removed).

        Phase overview functionality is now in Event Mode.
        """
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/tournaments/{fake_id}/phase")

        # Route should no longer exist (consolidated into Event Mode)
        assert response.status_code == 404

    def test_old_advance_route_removed(self, unauthenticated_client):
        """POST /tournaments/{id}/advance returns 404 (route removed).

        Phase advancement is now done via /event/{id}/advance.
        """
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/tournaments/{fake_id}/advance")

        # Route should no longer exist (consolidated into Event Mode)
        assert response.status_code == 404


class TestEventModeAdvanceExists:
    """Tests that new Event Mode advance route exists."""

    def test_event_advance_requires_auth(self, unauthenticated_client):
        """POST /event/{id}/advance requires authentication.

        This is the new consolidated route for phase advancement.
        """
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/event/{fake_id}/advance")

        # Should require authentication (401 or redirect)
        assert response.status_code in [401, 302, 303]
