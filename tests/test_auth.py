"""Tests for authentication system."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import magic_link_auth
from app.config import settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestMagicLinkAuth:
    """Tests for magic link authentication."""

    def test_generate_token(self):
        """Test token generation."""
        token = magic_link_auth.generate_token("test@example.com", "admin")
        assert token
        assert isinstance(token, str)

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        token = magic_link_auth.generate_token("test@example.com", "admin")
        payload = magic_link_auth.verify_token(token)

        assert payload is not None
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"
        assert "created_at" in payload

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        payload = magic_link_auth.verify_token("invalid-token")
        assert payload is None

    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        import time

        token = magic_link_auth.generate_token("test@example.com", "admin")
        # Wait 2 seconds, then verify with max_age=1 to simulate expiration
        time.sleep(2)
        payload = magic_link_auth.verify_token(token, max_age=1)
        assert payload is None

    def test_generate_magic_link(self):
        """Test generating complete magic link URL."""
        link = magic_link_auth.generate_magic_link("test@example.com", "admin")

        assert link.startswith(settings.MAGIC_LINK_BASE_URL)
        assert "/auth/verify?token=" in link


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page(self, client):
        """Test login page is accessible."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"Login" in response.content
        assert b"email" in response.content.lower()

    def test_send_magic_link_existing_user(self, client):
        """Test sending magic link to existing user."""
        response = client.post(
            "/auth/send-magic-link",
            data={"email": "admin@battle-d.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_send_magic_link_nonexistent_user(self, client):
        """Test sending magic link to non-existent user (same response for security)."""
        response = client.post(
            "/auth/send-magic-link",
            data={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_verify_valid_magic_link(self, client):
        """Test verifying a valid magic link."""
        # Generate a token for existing user
        token = magic_link_auth.generate_token("admin@battle-d.com", "admin")

        response = client.get(
            f"/auth/verify?token={token}",
            follow_redirects=False,
        )

        assert response.status_code == 303  # Redirect
        assert response.headers["location"] == "/dashboard"

        # Check session cookie was set
        cookies = response.cookies
        assert settings.SESSION_COOKIE_NAME in cookies

    def test_verify_invalid_magic_link(self, client):
        """Test verifying an invalid magic link."""
        response = client.get("/auth/verify?token=invalid-token")
        assert response.status_code == 401

    def test_logout(self, client):
        """Test logout clears session."""
        # First login
        token = magic_link_auth.generate_token("admin@battle-d.com", "admin")
        client.get(f"/auth/verify?token={token}")

        # Then logout
        response = client.get("/auth/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/auth/login"

    def test_dashboard_requires_auth(self, client):
        """Test dashboard requires authentication."""
        response = client.get("/dashboard")
        assert response.status_code == 401

    def test_dashboard_with_auth(self, client):
        """Test dashboard is accessible when authenticated."""
        # Login first
        token = magic_link_auth.generate_token("admin@battle-d.com", "admin")
        login_response = client.get(f"/auth/verify?token={token}", follow_redirects=False)

        # Extract session cookie from Set-Cookie header
        set_cookie_header = login_response.headers.get("set-cookie", "")
        assert settings.SESSION_COOKIE_NAME in set_cookie_header

        # Parse cookie value
        cookie_start = set_cookie_header.find(f"{settings.SESSION_COOKIE_NAME}=") + len(
            f"{settings.SESSION_COOKIE_NAME}="
        )
        cookie_end = set_cookie_header.find(";", cookie_start)
        session_cookie = set_cookie_header[cookie_start:cookie_end]

        # Access dashboard with session
        response = client.get(
            "/dashboard", cookies={settings.SESSION_COOKIE_NAME: session_cookie}
        )
        assert response.status_code == 200
        assert b"Dashboard" in response.content
        assert b"admin@battle-d.com" in response.content


class TestSessionManagement:
    """Tests for session management."""

    def test_session_persists_across_requests(self, client):
        """Test session cookie works across multiple requests."""
        # Login
        token = magic_link_auth.generate_token("staff@battle-d.com", "staff")
        login_response = client.get(f"/auth/verify?token={token}", follow_redirects=False)

        # Extract session cookie from Set-Cookie header
        set_cookie_header = login_response.headers.get("set-cookie", "")
        cookie_start = set_cookie_header.find(f"{settings.SESSION_COOKIE_NAME}=") + len(
            f"{settings.SESSION_COOKIE_NAME}="
        )
        cookie_end = set_cookie_header.find(";", cookie_start)
        session_cookie = set_cookie_header[cookie_start:cookie_end]

        # Make multiple requests with same session
        for _ in range(3):
            response = client.get(
                "/dashboard", cookies={settings.SESSION_COOKIE_NAME: session_cookie}
            )
            assert response.status_code == 200

    def test_invalid_session_rejected(self, client):
        """Test invalid session is rejected."""
        response = client.get(
            "/dashboard",
            cookies={settings.SESSION_COOKIE_NAME: "invalid-session"},
        )
        assert response.status_code == 401
