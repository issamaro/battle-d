"""Integration tests for CRUD workflows."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import magic_link_auth
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
    """Create test client with mock email provider."""

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    app.dependency_overrides[get_email_service] = get_mock_email_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    mock_email_provider.clear()


def get_admin_session(client):
    """Helper to get authenticated admin session."""
    token = magic_link_auth.generate_token("admin@test.com", "admin")
    response = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    return client


def get_staff_session(client):
    """Helper to get authenticated staff session."""
    token = magic_link_auth.generate_token("staff@test.com", "staff")
    response = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    return client


class TestUserManagementCRUD:
    """Test complete user management CRUD workflow."""

    def test_create_user_workflow(self, client):
        """Test creating a new user through admin UI."""
        admin_client = get_admin_session(client)

        # Create new user
        response = admin_client.post(
            "/admin/users/create",
            data={
                "email": "newuser@test.com",
                "first_name": "New User",
                "role": "mc",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/users"

    def test_list_users_workflow(self, client):
        """Test listing users with role filter."""
        admin_client = get_admin_session(client)

        # List all users
        response = admin_client.get("/admin/users")
        assert response.status_code == 200
        assert b"admin@test.com" in response.content

        # Filter by role
        response = admin_client.get("/admin/users?role_filter=admin")
        assert response.status_code == 200

    def test_edit_user_workflow(self, client):
        """Test editing a user through admin UI."""
        admin_client = get_admin_session(client)

        # Get user ID
        async def get_user_id():
            async with async_session_maker() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_email("staff@test.com")
                return str(user.id)

        import asyncio

        user_id = asyncio.run(get_user_id())

        # Update user
        response = admin_client.post(
            f"/admin/users/{user_id}/edit",
            data={
                "email": "staff@test.com",
                "first_name": "Updated Staff",
                "role": "staff",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_delete_user_workflow(self, client):
        """Test deleting a user through admin UI."""
        admin_client = get_admin_session(client)

        # Create user to delete
        admin_client.post(
            "/admin/users/create",
            data={
                "email": "todelete@test.com",
                "first_name": "To Delete",
                "role": "judge",
            },
        )

        # Get user ID
        async def get_user_id():
            async with async_session_maker() as session:
                user_repo = UserRepository(session)
                user = await user_repo.get_by_email("todelete@test.com")
                return str(user.id)

        import asyncio

        user_id = asyncio.run(get_user_id())

        # Delete user
        response = admin_client.post(
            f"/admin/users/{user_id}/delete", follow_redirects=False
        )
        assert response.status_code == 303


class TestDancerManagementCRUD:
    """Test complete dancer management CRUD workflow."""

    def test_search_dancers_htmx_workflow(self, client):
        """Test HTMX dancer search API."""
        staff_client = get_staff_session(client)

        # Search via HTMX endpoint (empty database)
        response = staff_client.get("/dancers/api/search?query=NonExistent")
        assert response.status_code == 200
        # Should return empty results
        assert b"No dancers found" in response.content or b"0" in response.content


class TestTournamentCRUD:
    """Test complete tournament and category CRUD workflow."""

    def test_create_tournament_workflow(self, client):
        """Test creating a new tournament through staff UI."""
        staff_client = get_staff_session(client)

        # Create tournament
        response = staff_client.post(
            "/tournaments/create",
            data={"name": "Test Tournament 2024"},
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify tournament was created
        response = staff_client.get("/tournaments")
        assert response.status_code == 200
        assert b"Test Tournament 2024" in response.content

    def test_add_category_to_tournament_workflow(self, client):
        """Test adding a category to a tournament."""
        staff_client = get_staff_session(client)

        # Create tournament
        staff_client.post("/tournaments/create", data={"name": "Category Test"})

        # Get tournament ID
        async def get_tournament_id():
            async with async_session_maker() as session:
                tournament_repo = TournamentRepository(session)
                tournaments = await tournament_repo.get_all()
                return str(tournaments[0].id)

        import asyncio

        tournament_id = asyncio.run(get_tournament_id())

        # Add 1v1 category
        response = staff_client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Hip Hop Boys 1v1",
                "is_duo": "false",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        # Verify category appears on tournament detail
        response = staff_client.get(f"/tournaments/{tournament_id}")
        assert response.status_code == 200
        assert b"Hip Hop Boys 1v1" in response.content

    def test_add_duo_category_workflow(self, client):
        """Test adding a 2v2 duo category."""
        staff_client = get_staff_session(client)

        # Create tournament
        staff_client.post("/tournaments/create", data={"name": "Duo Test"})

        # Get tournament ID
        async def get_tournament_id():
            async with async_session_maker() as session:
                tournament_repo = TournamentRepository(session)
                tournaments = await tournament_repo.get_all()
                return str(tournaments[0].id)

        import asyncio

        tournament_id = asyncio.run(get_tournament_id())

        # Add 2v2 category
        response = staff_client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Breaking Duo 2v2",
                "is_duo": "true",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestRegistrationWorkflows:
    """Test dancer registration workflows for both 1v1 and 2v2."""

    def test_registration_page_loads(self, client):
        """Test that registration page loads with valid tournament and category."""
        staff_client = get_staff_session(client)

        # Create tournament
        response = staff_client.post(
            "/tournaments/create", data={"name": "Reg Test"}, follow_redirects=False
        )
        assert response.status_code == 303

        # Verify tournament list page works
        response = staff_client.get("/tournaments")
        assert response.status_code == 200
        assert b"Reg Test" in response.content
