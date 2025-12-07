"""Tests for phases routes.

Tests phase navigation and advancement functionality.
See: VALIDATION_RULES.md Phase Transition Validation
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def unauthenticated_client():
    """Create test client without authentication."""
    return TestClient(app)


class TestPhasesRouteExists:
    """Tests that routes exist at correct paths."""

    def test_phases_prefix_route_does_not_exist(self, unauthenticated_client):
        """Route /phases/{id}/phase should NOT exist."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/phases/{fake_id}/phase")

        # This route should NOT exist - expect 404 (not 401)
        # Even without auth, the route should return 404 if route doesn't exist
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


class TestPhasesRouteAuth:
    """Tests authentication requirements for phases routes."""

    def test_phases_overview_requires_auth(self, unauthenticated_client):
        """GET /tournaments/{id}/phase requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.get(f"/tournaments/{fake_id}/phase")

        # Should require auth (401)
        assert response.status_code == 401

    def test_phases_advance_requires_auth(self, unauthenticated_client):
        """POST /tournaments/{id}/advance requires authentication."""
        fake_id = uuid.uuid4()
        response = unauthenticated_client.post(f"/tournaments/{fake_id}/advance")

        # Should require auth (401)
        assert response.status_code == 401
