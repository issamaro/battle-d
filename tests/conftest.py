"""Shared test configuration and fixtures."""
import uuid
from datetime import date
from typing import Optional

import pytest
import pytest_asyncio
from app.db.database import init_db, drop_db, async_session_maker
from app.models import TournamentPhase, TournamentStatus
from app.models.dancer import Dancer
from app.models.tournament import Tournament
from app.models.category import Category
from app.models.performer import Performer
from app.repositories.dancer import DancerRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    """Setup and teardown test database for each test.

    This fixture automatically runs before and after each test function.
    It ensures a clean database state for every test.
    """
    # Ensure clean state by dropping any existing tables
    await drop_db()

    # Create all tables fresh
    await init_db()

    yield

    # Clean up after test
    await drop_db()


# =============================================================================
# SESSION FACTORY FIXTURE
# =============================================================================


@pytest.fixture
def async_session():
    """Provide async_session_maker for integration tests."""
    return async_session_maker


# =============================================================================
# FACTORY FIXTURES FOR INTEGRATION TESTS
# =============================================================================


@pytest.fixture
def create_test_dancer():
    """Factory fixture to create test dancers.

    Usage:
        dancer = await create_test_dancer()
        dancer = await create_test_dancer(email="custom@test.com", blaze="Custom")
    """
    async def _create(
        email: Optional[str] = None,
        first_name: str = "Test",
        last_name: str = "Dancer",
        date_of_birth: Optional[date] = None,
        blaze: Optional[str] = None,
        country: str = "France",
        city: str = "Paris",
    ) -> Dancer:
        async with async_session_maker() as session:
            dancer_repo = DancerRepository(session)

            # Generate unique values if not provided
            unique_id = uuid.uuid4().hex[:8]
            if email is None:
                email = f"dancer_{unique_id}@test.com"
            if blaze is None:
                blaze = f"B-Boy {unique_id}"
            if date_of_birth is None:
                date_of_birth = date(2000, 1, 1)

            dancer = await dancer_repo.create_dancer(
                email=email,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                blaze=blaze,
                country=country,
                city=city,
            )
            return dancer

    return _create


@pytest.fixture
def create_test_tournament():
    """Factory fixture to create test tournaments.

    Usage:
        tournament = await create_test_tournament()
        tournament = await create_test_tournament(name="Custom", phase=TournamentPhase.PRESELECTION)
    """
    async def _create(
        name: Optional[str] = None,
        phase: TournamentPhase = TournamentPhase.REGISTRATION,
        status: TournamentStatus = TournamentStatus.CREATED,
    ) -> Tournament:
        async with async_session_maker() as session:
            tournament_repo = TournamentRepository(session)

            # Generate unique name if not provided
            if name is None:
                name = f"Tournament {uuid.uuid4().hex[:8]}"

            tournament = await tournament_repo.create_tournament(name=name)

            # Set phase/status if different from defaults
            if phase != TournamentPhase.REGISTRATION or status != TournamentStatus.CREATED:
                tournament = await tournament_repo.update(
                    tournament.id,
                    phase=phase,
                    status=status,
                )

            return tournament

    return _create


@pytest.fixture
def create_test_category():
    """Factory fixture to create test categories.

    Usage:
        category = await create_test_category(tournament_id)
        category = await create_test_category(tournament_id, name="2v2", is_duo=True)
    """
    async def _create(
        tournament_id: uuid.UUID,
        name: Optional[str] = None,
        is_duo: bool = False,
        groups_ideal: int = 2,
        performers_ideal: int = 4,
    ) -> Category:
        async with async_session_maker() as session:
            category_repo = CategoryRepository(session)

            # Generate unique name if not provided
            if name is None:
                name = f"Category {uuid.uuid4().hex[:8]}"

            category = await category_repo.create_category(
                tournament_id=tournament_id,
                name=name,
                is_duo=is_duo,
                groups_ideal=groups_ideal,
                performers_ideal=performers_ideal,
            )
            return category

    return _create


@pytest.fixture
def create_test_performer():
    """Factory fixture to create test performers.

    Usage:
        performer = await create_test_performer(tournament_id, category_id, dancer_id)
        performer = await create_test_performer(tournament_id, category_id, dancer_id, partner_id=partner.id)
    """
    async def _create(
        tournament_id: uuid.UUID,
        category_id: uuid.UUID,
        dancer_id: uuid.UUID,
        partner_id: Optional[uuid.UUID] = None,
        duo_name: Optional[str] = None,
    ) -> Performer:
        async with async_session_maker() as session:
            performer_repo = PerformerRepository(session)

            performer = await performer_repo.create_performer(
                tournament_id=tournament_id,
                category_id=category_id,
                dancer_id=dancer_id,
                partner_id=partner_id,
                duo_name=duo_name,
            )
            return performer

    return _create
