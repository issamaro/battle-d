"""Integration tests for EventService.

These tests use REAL repositories and database to catch bugs like:
- Invalid enum references
- Method signature mismatches
- Relationship issues (battle.performers)

See: TESTING.md §Service Integration Tests
"""
import pytest
from datetime import date
from uuid import uuid4

from app.db.database import async_session_maker
from app.repositories.tournament import TournamentRepository
from app.repositories.category import CategoryRepository
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository
from app.repositories.dancer import DancerRepository
from app.services.event_service import EventService, CommandCenterContext
from app.models import TournamentPhase, TournamentStatus
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_event_service(session) -> EventService:
    """Helper to create an EventService with real repositories."""
    return EventService(
        tournament_repo=TournamentRepository(session),
        category_repo=CategoryRepository(session),
        battle_repo=BattleRepository(session),
        performer_repo=PerformerRepository(session),
    )


async def create_tournament(session, name: str = None) -> "Tournament":
    """Helper to create a tournament for tests."""
    tournament_repo = TournamentRepository(session)
    if name is None:
        name = f"Test Tournament {uuid4().hex[:8]}"
    tournament = await tournament_repo.create_tournament(name=name)
    # Activate it for event mode
    return await tournament_repo.update(tournament.id, status=TournamentStatus.ACTIVE)


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


async def create_battle(session, category_id, phase=BattlePhase.PRESELECTION,
                        status=BattleStatus.PENDING, sequence_order=1) -> Battle:
    """Helper to create a battle for tests."""
    battle_repo = BattleRepository(session)
    battle = Battle(
        category_id=category_id,
        phase=phase,
        status=status,
        sequence_order=sequence_order,
        outcome_type=BattleOutcomeType.SCORED,  # SCORED for preselection battles
    )
    return await battle_repo.create(battle)


# =============================================================================
# GET COMMAND CENTER CONTEXT TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_get_command_center_context_basic():
    """Test getting command center context with basic tournament."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        context = await service.get_command_center_context(tournament.id)

        assert context.tournament.id == tournament.id
        assert len(context.categories) == 1
        assert context.categories[0].name == category.name
        assert context.phase_display == "Registration"


@pytest.mark.asyncio
async def test_get_command_center_context_with_battles():
    """Test command center context includes pending battles in queue."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Create some battles
        battle1 = await create_battle(session, category.id, sequence_order=1)
        battle2 = await create_battle(session, category.id, sequence_order=2)

        # Advance tournament phase to match battle phase
        tournament_repo = TournamentRepository(session)
        await tournament_repo.update(tournament.id, phase=TournamentPhase.PRESELECTION)

        context = await service.get_command_center_context(tournament.id)

        # Should have battles in queue
        assert len(context.queue) == 2
        assert context.queue[0].position == 1
        assert context.queue[1].position == 2


@pytest.mark.asyncio
async def test_get_command_center_context_with_active_battle():
    """Test command center context detects active battles."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Create an active battle (without performers, just testing detection)
        battle_repo = BattleRepository(session)
        active_battle = Battle(
            category_id=category.id,
            phase=BattlePhase.PRESELECTION,
            status=BattleStatus.ACTIVE,
            sequence_order=1,
            outcome_type=BattleOutcomeType.SCORED,
        )
        active_battle = await battle_repo.create(active_battle)

        # Advance tournament phase
        tournament_repo = TournamentRepository(session)
        await tournament_repo.update(tournament.id, phase=TournamentPhase.PRESELECTION)

        context = await service.get_command_center_context(tournament.id)

        assert context.current_battle is not None
        assert context.current_battle.id == active_battle.id


@pytest.mark.asyncio
async def test_get_command_center_context_tournament_not_found():
    """Test command center context raises error for non-existent tournament."""
    async with async_session_maker() as session:
        service = create_event_service(session)
        fake_id = uuid4()

        with pytest.raises(ValueError) as exc_info:
            await service.get_command_center_context(fake_id)

        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_command_center_context_with_category_filter():
    """Test command center context with category filter."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category1 = await create_category(session, tournament.id)
        category2 = await create_category(session, tournament.id)

        # Create battles in each category
        await create_battle(session, category1.id, sequence_order=1)
        await create_battle(session, category2.id, sequence_order=2)

        # Advance tournament phase
        tournament_repo = TournamentRepository(session)
        await tournament_repo.update(tournament.id, phase=TournamentPhase.PRESELECTION)

        # Get context filtered to category1
        context = await service.get_command_center_context(
            tournament.id,
            category_id=category1.id,
        )

        # Queue should only have category1 battles
        assert len(context.queue) == 1


# =============================================================================
# GET PHASE PROGRESS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_get_phase_progress_empty():
    """Test phase progress with no battles."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)

        progress = await service.get_phase_progress(tournament.id)

        assert progress.completed == 0
        assert progress.total == 0
        assert progress.percentage == 0


@pytest.mark.asyncio
async def test_get_phase_progress_with_battles():
    """Test phase progress calculation with battles."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Create 4 battles: 2 completed, 2 pending
        await create_battle(session, category.id, status=BattleStatus.COMPLETED, sequence_order=1)
        await create_battle(session, category.id, status=BattleStatus.COMPLETED, sequence_order=2)
        await create_battle(session, category.id, status=BattleStatus.PENDING, sequence_order=3)
        await create_battle(session, category.id, status=BattleStatus.PENDING, sequence_order=4)

        # Advance tournament phase to PRESELECTION to match battles
        tournament_repo = TournamentRepository(session)
        await tournament_repo.update(tournament.id, phase=TournamentPhase.PRESELECTION)

        progress = await service.get_phase_progress(tournament.id)

        assert progress.total == 4
        assert progress.completed == 2
        assert progress.percentage == 50


@pytest.mark.asyncio
async def test_get_phase_progress_tournament_not_found():
    """Test phase progress with non-existent tournament."""
    async with async_session_maker() as session:
        service = create_event_service(session)
        fake_id = uuid4()

        progress = await service.get_phase_progress(fake_id)

        # Should return empty progress (not raise error)
        assert progress.completed == 0
        assert progress.total == 0


# =============================================================================
# GET BATTLE QUEUE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_get_battle_queue_empty():
    """Test battle queue with no battles."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)

        queue = await service.get_battle_queue(tournament.id)

        assert len(queue) == 0


@pytest.mark.asyncio
async def test_get_battle_queue_ordering():
    """Test battle queue is ordered by sequence_order."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Create battles out of order
        await create_battle(session, category.id, sequence_order=3)
        await create_battle(session, category.id, sequence_order=1)
        await create_battle(session, category.id, sequence_order=2)

        queue = await service.get_battle_queue(tournament.id)

        assert len(queue) == 3
        # Should be sorted by sequence_order
        assert queue[0].position == 1
        assert queue[1].position == 2
        assert queue[2].position == 3


@pytest.mark.asyncio
async def test_get_battle_queue_limit():
    """Test battle queue respects limit parameter."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Create 5 battles
        for i in range(5):
            await create_battle(session, category.id, sequence_order=i + 1)

        # Get only 2
        queue = await service.get_battle_queue(tournament.id, limit=2)

        assert len(queue) == 2


@pytest.mark.asyncio
async def test_get_battle_queue_excludes_completed():
    """Test battle queue excludes completed battles."""
    async with async_session_maker() as session:
        service = create_event_service(session)

        tournament = await create_tournament(session)
        category = await create_category(session, tournament.id)

        # Create mix of pending and completed battles
        await create_battle(session, category.id, status=BattleStatus.COMPLETED, sequence_order=1)
        await create_battle(session, category.id, status=BattleStatus.PENDING, sequence_order=2)
        await create_battle(session, category.id, status=BattleStatus.ACTIVE, sequence_order=3)

        queue = await service.get_battle_queue(tournament.id)

        # Only PENDING battles in queue
        assert len(queue) == 1
        assert queue[0].status == "pending"
