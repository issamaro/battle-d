"""E2E test fixtures.

Provides authenticated test clients and pre-built test scenarios.
Follows patterns from tests/test_crud_workflows.py.

IMPORTANT: E2E tests use the isolated in-memory test database from conftest.py.
This ensures tests NEVER affect the development database (./data/battle_d.db).

See: TESTING.md §End-to-End Tests
See: workbench/FEATURE_SPEC_2025-12-18_DATABASE-PURGE-BUG.md
"""
import pytest
import pytest_asyncio
from datetime import date
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.auth import magic_link_auth
from app.config import settings
from app.db.database import get_db
from app.repositories.user import UserRepository
from app.repositories.dancer import DancerRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.repositories.battle import BattleRepository
from app.models.user import UserRole
from app.models.tournament import TournamentPhase, TournamentStatus
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service

# Import the isolated test session maker from main conftest
from tests.conftest import _test_session_maker


# =============================================================================
# EMAIL MOCK (Reused from test_crud_workflows.py)
# =============================================================================


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


# =============================================================================
# TEST USERS
# =============================================================================


@pytest_asyncio.fixture(scope="function")
async def e2e_test_users():
    """Create test users for E2E tests (admin, staff, mc, judge)."""
    async with _test_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.create_user("admin@e2e-test.com", "Admin User", UserRole.ADMIN)
        await user_repo.create_user("staff@e2e-test.com", "Staff User", UserRole.STAFF)
        await user_repo.create_user("mc@e2e-test.com", "MC User", UserRole.MC)
        await user_repo.create_user("judge@e2e-test.com", "Judge User", UserRole.JUDGE)
        await session.commit()
    yield
    # Cleanup handled by setup_test_database fixture in main conftest.py


# =============================================================================
# SESSION COOKIE HELPER
# =============================================================================


def get_session_cookie(client: TestClient, email: str, role: str) -> str:
    """Login and extract session cookie.

    Reused from test_crud_workflows.py pattern.

    Args:
        client: TestClient instance
        email: User email
        role: User role

    Returns:
        Session cookie value
    """
    token = magic_link_auth.generate_token(email, role)
    response = client.get(f"/auth/verify?token={token}", follow_redirects=False)

    set_cookie_header = response.headers.get("set-cookie", "")
    cookie_name = settings.SESSION_COOKIE_NAME
    cookie_start = set_cookie_header.find(f"{cookie_name}=") + len(f"{cookie_name}=")
    cookie_end = set_cookie_header.find(";", cookie_start)
    return set_cookie_header[cookie_start:cookie_end]


# =============================================================================
# BASE TEST CLIENT
# =============================================================================


@pytest.fixture
def e2e_client(mock_email_provider):
    """Base test client with mocked email service and isolated test database.

    IMPORTANT: This fixture overrides the database dependency to use the
    isolated in-memory test database, preventing any changes to the
    development database (./data/battle_d.db).

    Note: Use authenticated client fixtures (admin_client, etc.) for most tests.
    """

    def get_mock_email_service():
        return EmailService(mock_email_provider)

    async def get_test_db():
        """Override database dependency to use test database."""
        async with _test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_email_service] = get_mock_email_service
    app.dependency_overrides[get_db] = get_test_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    mock_email_provider.clear()


# =============================================================================
# AUTHENTICATED CLIENTS
# =============================================================================


@pytest.fixture
def admin_client(e2e_client, e2e_test_users):
    """Test client authenticated as admin.

    Use for:
    - User management
    - Phase advancement
    - Tournament administration
    """
    cookie = get_session_cookie(e2e_client, "admin@e2e-test.com", "admin")
    e2e_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    return e2e_client


@pytest.fixture
def staff_client(e2e_client, e2e_test_users):
    """Test client authenticated as staff.

    Use for:
    - Tournament creation
    - Dancer management
    - Category management
    - Battle management
    """
    cookie = get_session_cookie(e2e_client, "staff@e2e-test.com", "staff")
    e2e_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    return e2e_client


@pytest.fixture
def mc_client(e2e_client, e2e_test_users):
    """Test client authenticated as MC.

    Use for:
    - Event mode command center
    - Battle queue viewing
    """
    cookie = get_session_cookie(e2e_client, "mc@e2e-test.com", "mc")
    e2e_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    return e2e_client


@pytest.fixture
def judge_client(e2e_client, e2e_test_users):
    """Test client authenticated as judge.

    Use for:
    - Judge-specific features (V2)
    """
    cookie = get_session_cookie(e2e_client, "judge@e2e-test.com", "judge")
    e2e_client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    return e2e_client


# =============================================================================
# TEST DATA FACTORIES
# =============================================================================


@pytest.fixture
def create_e2e_tournament():
    """Factory to create tournament with categories and performers.

    Returns a function that creates a complete tournament setup.

    Usage:
        data = await create_e2e_tournament()
        data = await create_e2e_tournament(phase=TournamentPhase.PRESELECTION)
        data = await create_e2e_tournament(num_categories=2, performers_per_category=8)
    """

    async def _create(
        name: str = None,
        phase: TournamentPhase = TournamentPhase.REGISTRATION,
        status: TournamentStatus = TournamentStatus.CREATED,
        num_categories: int = 1,
        performers_per_category: int = 4,
    ):
        """Create tournament with optional pre-populated data.

        Args:
            name: Tournament name (auto-generated if None)
            phase: Tournament phase
            status: Tournament status
            num_categories: Number of categories to create
            performers_per_category: Performers per category

        Returns:
            Dict with tournament, categories, dancers, performers
        """
        async with _test_session_maker() as session:
            # Create tournament
            tournament_repo = TournamentRepository(session)
            tournament = await tournament_repo.create_tournament(
                name=name or f"E2E Tournament {uuid4().hex[:8]}"
            )

            # Update phase/status if different from defaults
            updates = {}
            if phase != TournamentPhase.REGISTRATION:
                updates["phase"] = phase
            if status != TournamentStatus.CREATED:
                updates["status"] = status

            if updates:
                await tournament_repo.update(tournament.id, **updates)
                tournament = await tournament_repo.get_by_id(tournament.id)

            # Create categories
            category_repo = CategoryRepository(session)
            categories = []
            for i in range(num_categories):
                category = await category_repo.create_category(
                    tournament_id=tournament.id,
                    name=f"Category {i + 1}",
                    is_duo=False,
                    groups_ideal=2,
                    performers_ideal=4,
                )
                categories.append(category)

            # Create dancers and performers
            dancer_repo = DancerRepository(session)
            performer_repo = PerformerRepository(session)
            dancers = []
            performers = []

            for category in categories:
                for j in range(performers_per_category):
                    dancer = await dancer_repo.create_dancer(
                        email=f"dancer_{uuid4().hex[:8]}@test.com",
                        first_name="Dancer",
                        last_name=f"{j + 1}",
                        date_of_birth=date(2000, 1, 1),
                        blaze=f"B-Boy {uuid4().hex[:6]}",
                    )
                    dancers.append(dancer)

                    performer = await performer_repo.create_performer(
                        tournament_id=tournament.id,
                        category_id=category.id,
                        dancer_id=dancer.id,
                    )
                    performers.append(performer)

            await session.commit()

            # Re-fetch to get committed state
            tournament = await tournament_repo.get_by_id(tournament.id)

            return {
                "tournament": tournament,
                "categories": categories,
                "dancers": dancers,
                "performers": performers,
            }

    return _create


@pytest.fixture
def create_e2e_battle():
    """Factory to create battles for E2E tests.

    Usage:
        battle = await create_e2e_battle(category_id, BattlePhase.PRESELECTION, performers[:2])
        battle = await create_e2e_battle(category_id, BattlePhase.POOLS, performers[:2], BattleStatus.ACTIVE)
    """

    async def _create(
        category_id,
        phase: BattlePhase,
        performers,
        status: BattleStatus = BattleStatus.PENDING,
    ):
        """Create a battle with performers.

        Args:
            category_id: Category UUID
            phase: Battle phase
            performers: List of performers
            status: Battle status

        Returns:
            Battle instance
        """
        async with _test_session_maker() as session:
            battle_repo = BattleRepository(session)

            # Determine outcome type based on phase
            outcome_type_map = {
                BattlePhase.PRESELECTION: BattleOutcomeType.SCORED,
                BattlePhase.POOLS: BattleOutcomeType.WIN_DRAW_LOSS,
                BattlePhase.TIEBREAK: BattleOutcomeType.TIEBREAK,
                BattlePhase.FINALS: BattleOutcomeType.WIN_LOSS,
            }
            outcome_type = outcome_type_map.get(phase, BattleOutcomeType.WIN_LOSS)

            performer_ids = [p.id for p in performers]
            battle = await battle_repo.create_battle(
                category_id=category_id,
                phase=phase,
                outcome_type=outcome_type,
                performer_ids=performer_ids,
            )

            if status != BattleStatus.PENDING:
                await battle_repo.update(battle.id, status=status)

            await session.commit()

            # Re-fetch with performers loaded
            battle = await battle_repo.get_with_performers(battle.id)
            return battle

    return _create
