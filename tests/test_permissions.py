"""Tests for role-based permissions."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import magic_link_auth
from app.config import settings
from app.dependencies import CurrentUser
from app.db.database import get_db
from tests.conftest import test_session_maker


@pytest.fixture
def client():
    """Create test client with isolated test database."""
    async def get_test_db():
        """Override database dependency to use test database."""
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = get_test_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def get_session_cookie(email: str, role: str) -> str:
    """Generate session cookie for testing.

    Args:
        email: User email
        role: User role

    Returns:
        Session cookie value
    """
    token = magic_link_auth.generate_token(email, role)
    return token


class TestCurrentUser:
    """Tests for CurrentUser model."""

    def test_admin_permissions(self):
        """Test admin has all permissions."""
        user = CurrentUser("admin@test.com", "admin")

        assert user.is_admin is True
        assert user.is_staff is True
        assert user.is_mc is True
        assert user.is_judge is False

    def test_staff_permissions(self):
        """Test staff permissions."""
        user = CurrentUser("staff@test.com", "staff")

        assert user.is_admin is False
        assert user.is_staff is True
        assert user.is_mc is True
        assert user.is_judge is False

    def test_mc_permissions(self):
        """Test MC permissions."""
        user = CurrentUser("mc@test.com", "mc")

        assert user.is_admin is False
        assert user.is_staff is False
        assert user.is_mc is True
        assert user.is_judge is False

    def test_judge_permissions(self):
        """Test judge permissions."""
        user = CurrentUser("judge@test.com", "judge")

        assert user.is_admin is False
        assert user.is_staff is False
        assert user.is_mc is False
        assert user.is_judge is True


class TestRoleBasedAccess:
    """Tests for role-based access control."""

    def test_admin_overview_redirects_to_tournaments(self, client):
        """Test /overview redirects to /tournaments for admin."""
        session = get_session_cookie("admin@battle-d.com", "admin")
        response = client.get("/overview", cookies={settings.SESSION_COOKIE_NAME: session}, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/tournaments"

    def test_staff_overview_redirects_to_tournaments(self, client):
        """Test /overview redirects to /tournaments for staff."""
        session = get_session_cookie("staff@battle-d.com", "staff")
        response = client.get("/overview", cookies={settings.SESSION_COOKIE_NAME: session}, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/tournaments"

    def test_mc_overview_redirects_to_tournaments(self, client):
        """Test /overview redirects to /tournaments for MC."""
        session = get_session_cookie("mc@battle-d.com", "mc")
        response = client.get("/overview", cookies={settings.SESSION_COOKIE_NAME: session}, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/tournaments"

    def test_unauthenticated_overview_still_redirects(self, client):
        """Test /overview redirects even when unauthenticated (then auth check happens on /tournaments)."""
        response = client.get("/overview", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/tournaments"


@pytest.mark.skip(reason="Phase navigation migrated to database-driven - tests need rewriting")
class TestPhasePermissions:
    """Tests for tournament phase permissions.

    NOTE: These tests are for the legacy phase navigation system that used global variables.
    Phase navigation has been migrated to database-driven with TournamentService.
    These tests need to be rewritten to match the new architecture:
    - GET /tournaments/{id}/phase instead of GET /phases/
    - POST /tournaments/{id}/advance instead of POST /phases/advance
    - No go-back functionality (forward-only)
    - Requires tournament in database
    """

    def test_all_roles_can_view_phases(self, client):
        """Test all authenticated users can view phases."""
        roles = ["admin", "staff", "mc"]

        for role in roles:
            session = get_session_cookie(f"{role}@battle-d.com", role)
            response = client.get("/phases/", cookies={settings.SESSION_COOKIE_NAME: session})
            assert response.status_code == 200, f"{role} should be able to view phases"

    def test_admin_can_advance_phase(self, client):
        """Test only admin can advance tournament phase."""
        session = get_session_cookie("admin@battle-d.com", "admin")
        response = client.post("/phases/advance", cookies={settings.SESSION_COOKIE_NAME: session})
        assert response.status_code == 200

    def test_staff_cannot_advance_phase(self, client):
        """Test staff cannot advance tournament phase."""
        session = get_session_cookie("staff@battle-d.com", "staff")
        response = client.post("/phases/advance", cookies={settings.SESSION_COOKIE_NAME: session})
        assert response.status_code == 403

    def test_mc_cannot_advance_phase(self, client):
        """Test MC cannot advance tournament phase."""
        session = get_session_cookie("mc@battle-d.com", "mc")
        response = client.post("/phases/advance", cookies={settings.SESSION_COOKIE_NAME: session})
        assert response.status_code == 403

    def test_admin_can_go_back_phase(self, client):
        """Test only admin can go back phase."""
        # First advance to preselection
        session = get_session_cookie("admin@battle-d.com", "admin")
        client.post("/phases/advance", cookies={settings.SESSION_COOKIE_NAME: session})

        # Then go back
        response = client.post("/phases/go-back", cookies={settings.SESSION_COOKIE_NAME: session})
        assert response.status_code == 200

    def test_staff_cannot_go_back_phase(self, client):
        """Test staff cannot go back phase."""
        session = get_session_cookie("staff@battle-d.com", "staff")
        response = client.post("/phases/go-back", cookies={settings.SESSION_COOKIE_NAME: session})
        assert response.status_code == 403

    def test_all_roles_can_get_current_phase(self, client):
        """Test all authenticated users can get current phase."""
        roles = ["admin", "staff", "mc"]

        for role in roles:
            session = get_session_cookie(f"{role}@battle-d.com", role)
            response = client.get(
                "/phases/current", cookies={settings.SESSION_COOKIE_NAME: session}
            )
            assert response.status_code == 200, f"{role} should be able to get current phase"
            data = response.json()
            assert "phase" in data

    def test_unauthenticated_cannot_access_phases(self, client):
        """Test unauthenticated user cannot access phase endpoints."""
        endpoints = [
            "/phases/",
            "/phases/current",
            "/phases/advance",
            "/phases/go-back",
        ]

        for endpoint in endpoints:
            method = client.post if "advance" in endpoint or "go-back" in endpoint else client.get
            response = method(endpoint)
            assert response.status_code == 401, f"Unauthenticated should not access {endpoint}"
