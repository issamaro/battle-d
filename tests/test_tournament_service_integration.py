"""Integration tests for TournamentService.

These tests use REAL repositories and database to catch bugs like:
- Invalid enum references
- Method signature mismatches
- Relationship issues
- Phase transition validation

See: TESTING.md §Service Integration Tests
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.db.database import async_session_maker
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.performer import PerformerRepository
from app.repositories.battle import BattleRepository
from app.repositories.pool import PoolRepository
from app.repositories.dancer import DancerRepository
from app.services.tournament_service import TournamentService
from app.services.battle_service import BattleService
from app.services.pool_service import PoolService
from app.models import TournamentPhase, TournamentStatus
from app.models.battle import BattlePhase, BattleStatus, BattleOutcomeType
from app.exceptions import ValidationError


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_tournament_service(session) -> TournamentService:
    """Helper to create a TournamentService with real repositories."""
    battle_repo = BattleRepository(session)
    performer_repo = PerformerRepository(session)
    pool_repo = PoolRepository(session)

    return TournamentService(
        tournament_repo=TournamentRepository(session),
        category_repo=CategoryRepository(session),
        performer_repo=performer_repo,
        battle_repo=battle_repo,
        pool_repo=pool_repo,
        battle_service=BattleService(battle_repo, performer_repo),
        pool_service=PoolService(pool_repo, performer_repo),
    )


async def create_tournament(session, name: str = None) -> "Tournament":
    """Helper to create a tournament for tests."""
    tournament_repo = TournamentRepository(session)
    if name is None:
        name = f"Test Tournament {uuid4().hex[:8]}"
    return await tournament_repo.create_tournament(name=name)


async def create_category(session, tournament_id, is_duo: bool = False) -> "Category":
    """Helper to create a category for tests."""
    category_repo = CategoryRepository(session)
    return await category_repo.create_category(
        tournament_id=tournament_id,
        name=f"Test Category {uuid4().hex[:8]}",
        is_duo=is_duo,
        groups_ideal=2,
        performers_ideal=4,
    )


async def create_dancer(session, email: str, blaze: str) -> "Dancer":
    """Helper to create a dancer for tests."""
    dancer_repo = DancerRepository(session)
    return await dancer_repo.create_dancer(
        email=email,
        first_name="Test",
        last_name="Dancer",
        date_of_birth=date(2000, 1, 1),
        blaze=blaze,
    )


async def register_performer(session, tournament_id, category_id, dancer_id) -> "Performer":
    """Helper to register a performer for tests."""
    performer_repo = PerformerRepository(session)
    return await performer_repo.create_performer(
        tournament_id=tournament_id,
        category_id=category_id,
        dancer_id=dancer_id,
    )


# =============================================================================
# ADVANCE TOURNAMENT PHASE - BASIC TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_advance_from_registration_success():
    """Test successful phase advance from REGISTRATION to PRESELECTION."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)

        # Create tournament with category and sufficient performers
        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Need minimum 5 performers for groups_ideal=2: (2×2)+1=5
        for i in range(5):
            dancer = await create_dancer(session, f"dancer{i}@test.com", f"Dancer {i}")
            await register_performer(session, tournament.id, category.id, dancer.id)

        # Advance phase
        updated = await service.advance_tournament_phase(tournament.id)

        assert updated.phase == TournamentPhase.PRESELECTION
        assert updated.status == TournamentStatus.ACTIVE  # Auto-activated


@pytest.mark.asyncio
async def test_advance_auto_activates_tournament():
    """Test that tournament auto-activates when advancing from REGISTRATION."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)
        tournament_repo = TournamentRepository(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Verify starts in CREATED status
        assert tournament.status == TournamentStatus.CREATED

        # Register minimum performers
        for i in range(5):
            dancer = await create_dancer(session, f"dancer{i}@test.com", f"Dancer {i}")
            await register_performer(session, tournament.id, category.id, dancer.id)

        # Advance phase
        updated = await service.advance_tournament_phase(tournament.id)

        # Should be ACTIVE now
        assert updated.status == TournamentStatus.ACTIVE


@pytest.mark.asyncio
async def test_advance_tournament_not_found():
    """Test advance with non-existent tournament raises error."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)
        fake_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.advance_tournament_phase(fake_id)

        assert "not found" in str(exc_info.value).lower()


# =============================================================================
# VALIDATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_advance_fails_insufficient_performers():
    """Test that advance fails when category has insufficient performers."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Only register 3 performers (need 5 for groups_ideal=2)
        for i in range(3):
            dancer = await create_dancer(session, f"dancer{i}@test.com", f"Dancer {i}")
            await register_performer(session, tournament.id, category.id, dancer.id)

        with pytest.raises(ValidationError) as exc_info:
            await service.advance_tournament_phase(tournament.id)

        assert "minimum" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower() or "registered" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_advance_fails_another_tournament_active():
    """Test that advance fails when another tournament is already active."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)
        tournament_repo = TournamentRepository(session)

        # Create and activate first tournament
        tournament1 = await create_tournament(session, name="Tournament 1")
        category1 = await create_category(session, tournament1.id)
        for i in range(5):
            dancer = await create_dancer(session, f"t1_dancer{i}@test.com", f"T1 Dancer {i}")
            await register_performer(session, tournament1.id, category1.id, dancer.id)
        await service.advance_tournament_phase(tournament1.id)

        # Create second tournament
        tournament2 = await create_tournament(session, name="Tournament 2")
        category2 = await create_category(session, tournament2.id)
        for i in range(5):
            dancer = await create_dancer(session, f"t2_dancer{i}@test.com", f"T2 Dancer {i}")
            await register_performer(session, tournament2.id, category2.id, dancer.id)

        # Try to advance second tournament - should fail
        with pytest.raises(ValidationError) as exc_info:
            await service.advance_tournament_phase(tournament2.id)

        assert "already active" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_advance_fails_no_categories():
    """Test that advance fails when tournament has no categories."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)

        tournament = await create_tournament(session)
        # No categories created

        with pytest.raises(ValidationError) as exc_info:
            await service.advance_tournament_phase(tournament.id)

        # Should fail validation
        assert len(str(exc_info.value)) > 0


# =============================================================================
# GET PHASE VALIDATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_get_phase_validation_success():
    """Test getting phase validation result without advancing."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Register sufficient performers
        for i in range(5):
            dancer = await create_dancer(session, f"dancer{i}@test.com", f"Dancer {i}")
            await register_performer(session, tournament.id, category.id, dancer.id)

        result = await service.get_phase_validation(tournament.id)

        # Should be valid (no errors)
        assert bool(result) is True
        assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_get_phase_validation_with_errors():
    """Test getting phase validation with insufficient performers."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Only 2 performers (insufficient)
        for i in range(2):
            dancer = await create_dancer(session, f"dancer{i}@test.com", f"Dancer {i}")
            await register_performer(session, tournament.id, category.id, dancer.id)

        result = await service.get_phase_validation(tournament.id)

        # Should have errors
        assert bool(result) is False
        assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_get_phase_validation_tournament_not_found():
    """Test get_phase_validation with non-existent tournament."""
    async with async_session_maker() as session:
        service = create_tournament_service(session)
        fake_id = uuid4()

        with pytest.raises(ValidationError) as exc_info:
            await service.get_phase_validation(fake_id)

        assert "not found" in str(exc_info.value).lower()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_completed_tournament_cannot_advance():
    """Test that completed tournament cannot advance further."""
    async with async_session_maker() as session:
        tournament_repo = TournamentRepository(session)
        service = create_tournament_service(session)

        # Create tournament in COMPLETED phase
        tournament = await create_tournament(session)
        await tournament_repo.update(
            tournament.id,
            phase=TournamentPhase.COMPLETED,
            status=TournamentStatus.COMPLETED,
        )

        with pytest.raises(ValidationError) as exc_info:
            await service.advance_tournament_phase(tournament.id)

        assert "completed" in str(exc_info.value).lower()
