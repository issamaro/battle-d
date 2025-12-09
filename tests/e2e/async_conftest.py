"""Async E2E test fixtures using httpx.AsyncClient with session override.

This module solves the session isolation problem:
- Fixtures create data in a shared session
- Routes use the same session via dependency override
- All data is visible throughout the test

Usage:
    @pytest.mark.asyncio
    async def test_with_fixture_data(async_e2e_session, async_client_factory):
        # Create test data
        tournament = await create_tournament(async_e2e_session)
        await async_e2e_session.flush()

        # Get authenticated client
        async with async_client_factory("staff") as client:
            response = await client.get(f"/tournaments/{tournament.id}")
            assert response.status_code == 200

See: TESTING.md §Async E2E Tests (Session Sharing Pattern)
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import date
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.database import async_session_maker, get_db
from app.repositories.user import UserRepository
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.dancer import DancerRepository
from app.repositories.performer import PerformerRepository
from app.repositories.battle import BattleRepository
from app.models.user import UserRole
from app.models.tournament import TournamentPhase, TournamentStatus
from app.models.battle import BattlePhase, BattleStatus, BattleOutcomeType
from app.auth import magic_link_auth
from app.config import settings
from app.services.email.service import EmailService
from app.services.email.provider import BaseEmailProvider
from app.dependencies import get_email_service


# =============================================================================
# MOCK EMAIL PROVIDER
# =============================================================================


class MockEmailProvider(BaseEmailProvider):
    """Mock email provider for async E2E tests."""

    def __init__(self):
        self.sent_emails = []

    async def send_magic_link(
        self, to_email: str, magic_link: str, first_name: str
    ) -> bool:
        self.sent_emails.append({
            "to_email": to_email,
            "magic_link": magic_link,
            "first_name": first_name
        })
        return True

    def clear(self):
        self.sent_emails = []


# =============================================================================
# CORE SESSION FIXTURE
# =============================================================================


@pytest_asyncio.fixture
async def async_e2e_session() -> AsyncGenerator[AsyncSession, None]:
    """Shared async session for E2E tests.

    This session is shared between:
    - Test fixture data creation
    - HTTP routes (via dependency override)

    Data created here IS visible to routes because they share the session.

    Uses flush() instead of commit() to keep data in transaction.
    Transaction rolls back at end for automatic cleanup.
    """
    async with async_session_maker() as session:
        yield session
        # Rollback at end - no need to clean up manually
        await session.rollback()


# =============================================================================
# ASYNC CLIENT FACTORY
# =============================================================================


@pytest.fixture
def async_client_factory(async_e2e_session: AsyncSession):
    """Factory to create authenticated AsyncClient instances.

    Usage:
        async with async_client_factory("staff") as client:
            response = await client.get("/tournaments")

    Available roles: "admin", "staff", "mc", "judge"
    """
    mock_email = MockEmailProvider()

    @asynccontextmanager
    async def _create_client(role: str = "staff"):
        """Create an authenticated async client.

        Args:
            role: User role (admin, staff, mc, judge)

        Yields:
            AsyncClient with authentication cookies
        """
        # Override get_db to return shared session
        async def override_get_db():
            yield async_e2e_session

        def get_mock_email_service():
            return EmailService(mock_email)

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_email_service] = get_mock_email_service

        try:
            # Generate auth token
            email = f"{role}@async-e2e-test.com"
            token = magic_link_auth.generate_token(email, role)

            # Create client
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test"
            ) as client:
                # Verify token to get session cookie
                await client.get(
                    f"/auth/verify?token={token}",
                    follow_redirects=False
                )

                # Client now has auth cookie
                yield client

        finally:
            app.dependency_overrides.clear()
            mock_email.clear()

    return _create_client


# =============================================================================
# DATA FACTORY FIXTURES
# =============================================================================


@pytest.fixture
def create_async_tournament(async_e2e_session: AsyncSession):
    """Factory to create tournaments in async E2E tests.

    Usage:
        tournament = await create_async_tournament(name="Summer Battle")
        tournament = await create_async_tournament(phase=TournamentPhase.PRESELECTION)
    """
    async def _create(
        name: str = None,
        phase: TournamentPhase = None,
        status: TournamentStatus = None,
    ):
        tournament_repo = TournamentRepository(async_e2e_session)

        name = name or f"Async E2E Tournament {uuid4().hex[:8]}"
        tournament = await tournament_repo.create_tournament(name=name)

        # Update phase/status if specified
        updates = {}
        if phase is not None:
            updates["phase"] = phase
        if status is not None:
            updates["status"] = status

        if updates:
            tournament = await tournament_repo.update(tournament.id, **updates)

        await async_e2e_session.flush()
        return tournament

    return _create


@pytest.fixture
def create_async_category(async_e2e_session: AsyncSession):
    """Factory to create categories in async E2E tests."""
    async def _create(
        tournament_id,
        name: str = None,
        is_duo: bool = False,
        groups_ideal: int = 2,
        performers_ideal: int = 4,
    ):
        category_repo = CategoryRepository(async_e2e_session)

        name = name or f"Category {uuid4().hex[:8]}"
        category = await category_repo.create_category(
            tournament_id=tournament_id,
            name=name,
            is_duo=is_duo,
            groups_ideal=groups_ideal,
            performers_ideal=performers_ideal,
        )

        await async_e2e_session.flush()
        return category

    return _create


@pytest.fixture
def create_async_performer(async_e2e_session: AsyncSession):
    """Factory to create performers (with dancers) in async E2E tests."""
    async def _create(
        tournament_id,
        category_id,
        blaze: str = None,
    ):
        dancer_repo = DancerRepository(async_e2e_session)
        performer_repo = PerformerRepository(async_e2e_session)

        # Create dancer
        unique_id = uuid4().hex[:8]
        dancer = await dancer_repo.create_dancer(
            email=f"dancer_{unique_id}@test.com",
            first_name="Dancer",
            last_name=unique_id,
            date_of_birth=date(2000, 1, 1),
            blaze=blaze or f"B-Boy {unique_id}",
        )

        # Create performer
        performer = await performer_repo.create_performer(
            tournament_id=tournament_id,
            category_id=category_id,
            dancer_id=dancer.id,
        )

        await async_e2e_session.flush()
        return performer, dancer

    return _create


@pytest.fixture
def create_async_battle(async_e2e_session: AsyncSession):
    """Factory to create battles in async E2E tests."""
    async def _create(
        category_id,
        phase: BattlePhase,
        performer_ids: list,
        status: BattleStatus = None,
    ):
        battle_repo = BattleRepository(async_e2e_session)

        # Determine outcome type based on phase
        outcome_type_map = {
            BattlePhase.PRESELECTION: BattleOutcomeType.SCORED,
            BattlePhase.POOLS: BattleOutcomeType.WIN_DRAW_LOSS,
            BattlePhase.TIEBREAK: BattleOutcomeType.TIEBREAK,
            BattlePhase.FINALS: BattleOutcomeType.WIN_LOSS,
        }
        outcome_type = outcome_type_map.get(phase, BattleOutcomeType.WIN_LOSS)

        battle = await battle_repo.create_battle(
            category_id=category_id,
            phase=phase,
            outcome_type=outcome_type,
            performer_ids=performer_ids,
        )

        if status is not None and status != BattleStatus.PENDING:
            await battle_repo.update(battle.id, status=status)

        await async_e2e_session.flush()

        # Re-fetch with performers
        battle = await battle_repo.get_with_performers(battle.id)
        return battle

    return _create


# =============================================================================
# COMPLETE SCENARIO FACTORY
# =============================================================================


@pytest.fixture
def create_async_tournament_scenario(
    async_e2e_session: AsyncSession,
    create_async_tournament,
    create_async_category,
    create_async_performer,
):
    """Factory to create complete tournament scenarios for E2E tests.

    Usage:
        data = await create_async_tournament_scenario(
            phase=TournamentPhase.PRESELECTION,
            num_categories=2,
            performers_per_category=8
        )

        # Access data
        data["tournament"]
        data["categories"][0]
        data["performers"][0]
    """
    async def _create(
        name: str = None,
        phase: TournamentPhase = None,
        num_categories: int = 1,
        performers_per_category: int = 4,
    ):
        # Create tournament
        tournament = await create_async_tournament(
            name=name,
            phase=phase or TournamentPhase.REGISTRATION,
        )

        # Create categories and performers
        categories = []
        performers = []
        dancers = []

        for i in range(num_categories):
            category = await create_async_category(
                tournament_id=tournament.id,
                name=f"Category {i + 1}",
            )
            categories.append(category)

            for j in range(performers_per_category):
                performer, dancer = await create_async_performer(
                    tournament_id=tournament.id,
                    category_id=category.id,
                )
                performers.append(performer)
                dancers.append(dancer)

        return {
            "tournament": tournament,
            "categories": categories,
            "performers": performers,
            "dancers": dancers,
        }

    return _create
