"""Shared test configuration and fixtures.

IMPORTANT: Tests use an isolated in-memory SQLite database.
This ensures tests NEVER affect the development database (./data/battle_d.db).

See: workbench/FEATURE_SPEC_2025-12-18_DATABASE-PURGE-BUG.md
"""
import uuid
from datetime import date
from typing import Optional

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.database import Base
from app.models import TournamentPhase, TournamentStatus
from app.models.dancer import Dancer
from app.models.tournament import Tournament
from app.models.category import Category
from app.models.performer import Performer
from app.repositories.dancer import DancerRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository

# =============================================================================
# TEST DATABASE ISOLATION
# =============================================================================
# Use in-memory SQLite for tests - NEVER touches ./data/battle_d.db
# This prevents the "database purged on code change" bug.

# Create a separate in-memory engine for tests
_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
)

# Create test-specific session maker (internal)
_test_session_maker = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# =============================================================================
# PUBLIC API - Import this in test files!
# =============================================================================
# Use: from tests.conftest import test_session_maker
# DO NOT use: from app.db.database import async_session_maker (production!)

test_session_maker = _test_session_maker  # Public alias for test files


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    """Setup and teardown test database for each test.

    Uses an in-memory SQLite database that is completely isolated
    from the development database. Each test gets a fresh database.

    IMPORTANT: This fixture NEVER touches ./data/battle_d.db
    """
    # Import all models to register them with Base.metadata
    import app.models  # noqa: F401

    # Create all tables in the in-memory test database
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop all tables after test (in-memory DB is discarded anyway)
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# =============================================================================
# SESSION FACTORY FIXTURE
# =============================================================================


@pytest.fixture
def async_session():
    """Provide test session maker for integration tests.

    Returns the isolated in-memory test session maker, NOT the production one.
    """
    return _test_session_maker


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
        async with _test_session_maker() as session:
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
        async with _test_session_maker() as session:
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
        async with _test_session_maker() as session:
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
        async with _test_session_maker() as session:
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
