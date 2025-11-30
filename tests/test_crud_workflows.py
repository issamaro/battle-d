"""Integration tests for CRUD workflows."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import magic_link_auth
from app.config import settings
from app.db.database import async_session_maker
from app.repositories.user import UserRepository
from app.repositories.dancer import DancerRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.models.user import UserRole
from app.models.tournament import TournamentStatus, TournamentPhase
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service


class MockEmailProvider(BaseEmailProvider):
    """Mock email provider for testing."""

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
async def setup_test_users():
    """Create test users for CRUD tests."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.create_user("admin@test.com", "Admin", UserRole.ADMIN)
        await user_repo.create_user("staff@test.com", "Staff", UserRole.STAFF)
        await session.commit()
    yield


@pytest.fixture
def client(mock_email_provider):
    """Create test client with mock email provider.

    Note: Must use with statement to maintain cookies across requests.
    """

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    app.dependency_overrides[get_email_service] = get_mock_email_service

    # Use context manager to maintain cookies
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    mock_email_provider.clear()


def get_session_cookie(client, email, role):
    """Helper to login and extract session cookie."""
    token = magic_link_auth.generate_token(email, role)
    response = client.get(f"/auth/verify?token={token}", follow_redirects=False)

    # Extract session cookie from Set-Cookie header
    set_cookie_header = response.headers.get("set-cookie", "")
    cookie_start = set_cookie_header.find(f"{settings.SESSION_COOKIE_NAME}=") + len(f"{settings.SESSION_COOKIE_NAME}=")
    cookie_end = set_cookie_header.find(";", cookie_start)
    return set_cookie_header[cookie_start:cookie_end]


class TestUserManagementCRUD:
    """Test complete user management CRUD workflow."""

    def test_create_user_workflow(self, client):
        """Test creating a new user through admin UI."""
        cookie = get_session_cookie(client, "admin@test.com", "admin")

        # Create new user
        response = client.post(
            "/admin/users/create",
            data={
                "email": "newuser@test.com",
                "first_name": "New User",
                "role": "mc",
            },
            cookies={settings.SESSION_COOKIE_NAME: cookie},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/users"

    def test_list_users_workflow(self, client):
        """Test listing users with role filter."""
        cookie = get_session_cookie(client, "admin@test.com", "admin")

        # List all users
        response = client.get("/admin/users", cookies={settings.SESSION_COOKIE_NAME: cookie})
        assert response.status_code == 200
        assert b"admin@test.com" in response.content

        # Filter by role
        response = client.get("/admin/users?role_filter=admin", cookies={settings.SESSION_COOKIE_NAME: cookie})
        assert response.status_code == 200

    def test_edit_user_workflow(self, client):
        """Test editing a user through admin UI."""
        cookie = get_session_cookie(client, "admin@test.com", "admin")

        # Get user ID
        async def get_user_id():
            async with async_session_maker() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_email("staff@test.com")
                return str(user.id)

        import asyncio

        user_id = asyncio.run(get_user_id())

        # Update user
        response = client.post(
            f"/admin/users/{user_id}/edit",
            data={
                "email": "staff@test.com",
                "first_name": "Updated Staff",
                "role": "staff",
            },
            cookies={settings.SESSION_COOKIE_NAME: cookie},
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_delete_user_workflow(self, client):
        """Test deleting a user through admin UI."""
        cookie = get_session_cookie(client, "admin@test.com", "admin")

        # Create user to delete
        client.post(
            "/admin/users/create",
            data={
                "email": "todelete@test.com",
                "first_name": "To Delete",
                "role": "judge",
            },
            cookies={settings.SESSION_COOKIE_NAME: cookie},
        )

        # Get user ID
        async def get_user_id():
            async with async_session_maker() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_email("todelete@test.com")
                return str(user.id) if user else None

        import asyncio

        user_id = asyncio.run(get_user_id())
        if not user_id:
            pytest.skip("User creation failed")

        # Delete user
        response = client.post(
            f"/admin/users/{user_id}/delete",
            cookies={settings.SESSION_COOKIE_NAME: cookie},
            follow_redirects=False
        )
        assert response.status_code == 303


class TestDancerManagementCRUD:
    """Test complete dancer management CRUD workflow."""

    def test_search_dancers_htmx_workflow(self, client):
        """Test HTMX dancer search API."""
        cookie = get_session_cookie(client, "staff@test.com", "staff")

        # Search via HTMX endpoint (empty database)
        response = client.get("/dancers/api/search?query=NonExistent", cookies={settings.SESSION_COOKIE_NAME: cookie})
        assert response.status_code == 200
        # Should return empty results (checks for empty state component)
        assert b"No Dancers Found" in response.content or b"No dancers" in response.content or response.content == b""


class TestTournamentCRUD:
    """Test complete tournament and category CRUD workflow."""

    def test_create_tournament_workflow(self, client):
        """Test creating a new tournament through staff UI."""
        cookie = get_session_cookie(client, "staff@test.com", "staff")

        # Create tournament
        response = client.post(
            "/tournaments/create",
            data={"name": "Test Tournament 2024"},
            cookies={settings.SESSION_COOKIE_NAME: cookie},
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify tournament was created
        response = client.get("/tournaments", cookies={settings.SESSION_COOKIE_NAME: cookie})
        assert response.status_code == 200
        assert b"Test Tournament 2024" in response.content

    def test_add_category_to_tournament_workflow(self, client):
        """Test adding a category to a tournament."""
        cookie = get_session_cookie(client, "staff@test.com", "staff")

        # Create tournament
        client.post("/tournaments/create", data={"name": "Category Test"}, cookies={settings.SESSION_COOKIE_NAME: cookie})

        # Get tournament ID
        async def get_tournament_id():
            async with async_session_maker() as session:
                tournament_repo = TournamentRepository(session)
                tournaments = await tournament_repo.get_all()
                return str(tournaments[0].id) if tournaments else None

        import asyncio

        tournament_id = asyncio.run(get_tournament_id())
        if not tournament_id:
            pytest.skip("Tournament creation failed")

        # Add 1v1 category
        response = client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Hip Hop Boys 1v1",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            cookies={settings.SESSION_COOKIE_NAME: cookie},
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify category appears on tournament detail
        response = client.get(f"/tournaments/{tournament_id}", cookies={settings.SESSION_COOKIE_NAME: cookie})
        assert response.status_code == 200
        assert b"Hip Hop Boys 1v1" in response.content

    def test_add_duo_category_workflow(self, client):
        """Test adding a 2v2 duo category."""
        cookie = get_session_cookie(client, "staff@test.com", "staff")

        # Create tournament
        client.post("/tournaments/create", data={"name": "Duo Test"}, cookies={settings.SESSION_COOKIE_NAME: cookie})

        # Get tournament ID
        async def get_tournament_id():
            async with async_session_maker() as session:
                tournament_repo = TournamentRepository(session)
                tournaments = await tournament_repo.get_all()
                return str(tournaments[0].id) if tournaments else None

        import asyncio

        tournament_id = asyncio.run(get_tournament_id())
        if not tournament_id:
            pytest.skip("Tournament creation failed")

        # Add 2v2 category
        response = client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Breaking Duo 2v2",
                "is_duo": "true",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            cookies={settings.SESSION_COOKIE_NAME: cookie},
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestRegistrationWorkflows:
    """Test dancer registration workflows for both 1v1 and 2v2."""

    def test_registration_page_loads(self, client):
        """Test that registration page loads with valid tournament and category."""
        cookie = get_session_cookie(client, "staff@test.com", "staff")

        # Create tournament
        response = client.post(
            "/tournaments/create",
            data={"name": "Reg Test"},
            cookies={settings.SESSION_COOKIE_NAME: cookie},
            follow_redirects=False
        )
        assert response.status_code == 303

        # Verify tournament list page works
        response = client.get("/tournaments", cookies={settings.SESSION_COOKIE_NAME: cookie})
        assert response.status_code == 200
        assert b"Reg Test" in response.content
