"""Tests for authentication system."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import magic_link_auth
from app.config import settings
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service
from app.db.database import async_session_maker
from app.repositories.user import UserRepository
from app.models.user import UserRole


class MockEmailProvider(BaseEmailProvider):
    """Mock email provider for testing.

    Stores sent emails in memory instead of actually sending them.
    """

    def __init__(self):
        self.sent_emails = []

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        """Mock email sending - just store the email data."""
        self.sent_emails.append(
            {"to_email": to_email, "magic_link": magic_link, "first_name": first_name}
        )
        return True

    def clear(self):
        """Clear sent emails list."""
        self.sent_emails = []


@pytest.fixture
def mock_email_provider():
    """Create mock email provider for testing."""
    return MockEmailProvider()


@pytest.fixture(scope="function", autouse=True)
async def setup_auth_test_users():
    """Create test users for auth tests.

    Note: Database setup is handled by conftest.py fixture.
    This fixture only creates the test users needed for auth tests.
    """
    # Create test users
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.create_user("admin@battle-d.com", "Admin", UserRole.ADMIN)
        await user_repo.create_user("staff@battle-d.com", "Staff", UserRole.STAFF)
        await user_repo.create_user("mc@battle-d.com", "MC", UserRole.MC)
        await session.commit()

    yield


@pytest.fixture
def client(mock_email_provider):
    """Create test client with mock email provider."""

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    # Override the email service dependency
    app.dependency_overrides[get_email_service] = get_mock_email_service

    client = TestClient(app)

    yield client

    # Clean up after test
    app.dependency_overrides.clear()
    mock_email_provider.clear()


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

        assert link.startswith(settings.BASE_URL)
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
        """Test sending magic link to existing user.

        Note: Email sending happens in background task after response.
        The email provider logic is tested separately in provider-specific tests.
        Routes now return redirects with flash messages instead of JSON.
        """
        response = client.post(
            "/auth/send-magic-link",
            data={"email": "admin@battle-d.com"},
            follow_redirects=False,
        )
        # Now returns redirect with flash message
        assert response.status_code == 303
        assert response.headers["location"] == "/auth/login"

    def test_send_magic_link_nonexistent_user(self, client):
        """Test sending magic link to non-existent user (same response for security).

        Note: No email is sent for non-existent users, but the response
        is intentionally the same to prevent user enumeration.
        Routes now return redirects with flash messages instead of JSON.
        """
        response = client.post(
            "/auth/send-magic-link",
            data={"email": "nonexistent@example.com"},
            follow_redirects=False,
        )
        # Same redirect for security (prevent user enumeration)
        assert response.status_code == 303
        assert response.headers["location"] == "/auth/login"

    def test_verify_valid_magic_link(self, client):
        """Test verifying a valid magic link."""
        # Generate a token for existing user
        token = magic_link_auth.generate_token("admin@battle-d.com", "admin")

        response = client.get(
            f"/auth/verify?token={token}",
            follow_redirects=False,
        )

        assert response.status_code == 303  # Redirect
        assert response.headers["location"] == "/overview"

        # Check session cookie was set
        cookies = response.cookies
        assert settings.SESSION_COOKIE_NAME in cookies

    def test_verify_invalid_magic_link(self, client):
        """Test verifying an invalid magic link.

        Routes now return redirects with flash messages instead of HTTP error codes.
        """
        response = client.get("/auth/verify?token=invalid-token", follow_redirects=False)
        # Now returns redirect to login with error flash message
        assert response.status_code == 303
        assert response.headers["location"] == "/auth/login"

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
        """Test overview page is accessible when authenticated."""
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

        # Access overview page with session
        response = client.get(
            "/overview", cookies={settings.SESSION_COOKIE_NAME: session_cookie}
        )
        assert response.status_code == 200
        assert b"Overview" in response.content
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
                "/overview", cookies={settings.SESSION_COOKIE_NAME: session_cookie}
            )
            assert response.status_code == 200

    def test_invalid_session_rejected(self, client):
        """Test invalid session is rejected."""
        response = client.get(
            "/overview",
            cookies={settings.SESSION_COOKIE_NAME: "invalid-session"},
        )
        assert response.status_code == 401
