"""Tests for BattleService.

Tests battle generation, lifecycle management, and queue operations.
See: ROADMAP.md §2.1 Battle Generation Services
"""
import pytest
import uuid
from typing import List
from unittest.mock import AsyncMock, MagicMock

from app.exceptions import ValidationError
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.models.performer import Performer
from app.models.pool import Pool
from app.repositories.battle import BattleRepository
from app.repositories.performer import PerformerRepository
from app.services.battle_service import BattleService


@pytest.fixture
def battle_repo():
    """Mock battle repository."""
    return AsyncMock(spec=BattleRepository)


@pytest.fixture
def performer_repo():
    """Mock performer repository."""
    return AsyncMock(spec=PerformerRepository)


@pytest.fixture
def battle_service(battle_repo, performer_repo):
    """Battle service with mocked repositories."""
    return BattleService(battle_repo, performer_repo)


@pytest.fixture
def tournament_id():
    """Sample tournament UUID."""
    return uuid.uuid4()


@pytest.fixture
def category_id():
    """Sample category UUID."""
    return uuid.uuid4()


@pytest.fixture
def pool_id():
    """Sample pool UUID."""
    return uuid.uuid4()


def create_performer(
    tournament_id: uuid.UUID, category_id: uuid.UUID, name: str = "Performer"
) -> Performer:
    """Helper to create a performer."""
    dancer_id = uuid.uuid4()
    performer = Performer(
        tournament_id=tournament_id,
        category_id=category_id,
        dancer_id=dancer_id,
    )
    performer.id = uuid.uuid4()
    return performer


def create_battle(
    category_id: uuid.UUID,
    phase: BattlePhase,
    status: BattleStatus,
    outcome_type: BattleOutcomeType,
    performers: List[Performer] = None,
) -> Battle:
    """Helper to create a battle."""
    battle = Battle(
        category_id=category_id,
        phase=phase,
        status=status,
        outcome_type=outcome_type,
    )
    battle.id = uuid.uuid4()
    if performers:
        battle.performers = performers
    return battle


class TestGeneratePreselectionBattles:
    """Tests for preselection battle generation."""

    async def test_even_number_of_performers(
        self, battle_service, performer_repo, battle_repo, tournament_id, category_id
    ):
        """Test preselection generation with even number of performers."""
        # Setup: 4 performers
        performers = [
            create_performer(tournament_id, category_id, f"Performer{i}")
            for i in range(4)
        ]
        performer_repo.get_by_category.return_value = performers

        # Mock battle creation - return a battle with assigned performers
        def create_battle_mock(battle):
            battle.id = uuid.uuid4()
            return battle

        battle_repo.create.side_effect = create_battle_mock

        # Execute
        battles = await battle_service.generate_preselection_battles(category_id)

        # Verify: 2 battles created (4 performers / 2)
        assert len(battles) == 2
        assert all(len(b.performers) == 2 for b in battles)
        assert all(b.phase == BattlePhase.PRESELECTION for b in battles)
        assert all(b.status == BattleStatus.PENDING for b in battles)
        assert all(b.outcome_type == BattleOutcomeType.SCORED for b in battles)

        # Verify all performers are included exactly once
        all_battle_performers = []
        for battle in battles:
            all_battle_performers.extend(battle.performers)
        assert len(all_battle_performers) == 4
        assert set(all_battle_performers) == set(performers)

    async def test_odd_number_of_performers(
        self, battle_service, performer_repo, battle_repo, tournament_id, category_id
    ):
        """Test preselection generation with odd number of performers."""
        # Setup: 5 performers
        performers = [
            create_performer(tournament_id, category_id, f"Performer{i}")
            for i in range(5)
        ]
        performer_repo.get_by_category.return_value = performers

        def create_battle_mock(battle):
            battle.id = uuid.uuid4()
            return battle

        battle_repo.create.side_effect = create_battle_mock

        # Execute
        battles = await battle_service.generate_preselection_battles(category_id)

        # Verify: 2 battles (one 1v1, one 3-way)
        assert len(battles) == 2

        # One should be 1v1, one should be 3-way
        battle_sizes = sorted([len(b.performers) for b in battles])
        assert battle_sizes == [2, 3]

        # Verify all performers included
        all_battle_performers = []
        for battle in battles:
            all_battle_performers.extend(battle.performers)
        assert len(all_battle_performers) == 5
        assert set(all_battle_performers) == set(performers)

    async def test_three_performers_only(
        self, battle_service, performer_repo, battle_repo, tournament_id, category_id
    ):
        """Test preselection with exactly 3 performers."""
        # Setup: 3 performers
        performers = [
            create_performer(tournament_id, category_id, f"Performer{i}")
            for i in range(3)
        ]
        performer_repo.get_by_category.return_value = performers

        def create_battle_mock(battle):
            battle.id = uuid.uuid4()
            return battle

        battle_repo.create.side_effect = create_battle_mock

        # Execute
        battles = await battle_service.generate_preselection_battles(category_id)

        # Verify: 1 three-way battle
        assert len(battles) == 1
        assert len(battles[0].performers) == 3

    async def test_no_performers_raises_error(
        self, battle_service, performer_repo, category_id
    ):
        """Test that no performers raises ValidationError."""
        performer_repo.get_by_category.return_value = []

        with pytest.raises(ValidationError, match="no performers in category"):
            await battle_service.generate_preselection_battles(category_id)


class TestGeneratePoolBattles:
    """Tests for pool battle generation."""

    async def test_round_robin_generation(
        self, battle_service, performer_repo, battle_repo, tournament_id, pool_id, category_id
    ):
        """Test round-robin pool battle generation."""
        # Setup: Pool with 4 performers
        performers = [
            create_performer(tournament_id, category_id, f"Performer{i}")
            for i in range(4)
        ]
        pool = Pool(category_id=category_id, name="Pool A")
        pool.id = pool_id
        pool.performers = performers
        pool.category_id = category_id

        performer_repo.get_pool_with_performers = AsyncMock(return_value=pool)

        def create_battle_mock(battle):
            battle.id = uuid.uuid4()
            return battle

        battle_repo.create.side_effect = create_battle_mock

        # Execute
        battles = await battle_service.generate_pool_battles(pool_id)

        # Verify: 6 battles (4 choose 2 = 6 combinations)
        assert len(battles) == 6
        assert all(len(b.performers) == 2 for b in battles)
        assert all(b.phase == BattlePhase.POOLS for b in battles)
        assert all(b.status == BattleStatus.PENDING for b in battles)
        assert all(b.outcome_type == BattleOutcomeType.WIN_DRAW_LOSS for b in battles)

        # Verify all unique pairings exist
        pairings = set()
        for battle in battles:
            p1, p2 = battle.performers
            pairing = tuple(sorted([p1.id, p2.id]))
            assert pairing not in pairings, "Duplicate pairing found"
            pairings.add(pairing)

    async def test_pool_not_found_raises_error(
        self, battle_service, performer_repo, pool_id
    ):
        """Test that missing pool raises ValidationError."""
        performer_repo.get_pool_with_performers = AsyncMock(return_value=None)

        with pytest.raises(ValidationError, match="Pool .* not found"):
            await battle_service.generate_pool_battles(pool_id)

    async def test_pool_no_performers_raises_error(
        self, battle_service, performer_repo, pool_id, category_id
    ):
        """Test that pool with no performers raises ValidationError."""
        pool = Pool(category_id=category_id, name="Pool A")
        pool.id = pool_id
        pool.performers = []
        performer_repo.get_pool_with_performers = AsyncMock(return_value=pool)

        with pytest.raises(ValidationError, match="has no performers"):
            await battle_service.generate_pool_battles(pool_id)


class TestGenerateFinalsBattles:
    """Tests for finals battle generation."""

    async def test_finals_generation_success(
        self, battle_service, performer_repo, battle_repo, tournament_id, category_id
    ):
        """Test finals battle generation with pool winners."""
        # Setup: 3 pool winners
        winners = [
            create_performer(tournament_id, category_id, f"Winner{i}")
            for i in range(3)
        ]
        performer_repo.get_pool_winners = AsyncMock(return_value=winners)

        def create_battle_mock(battle):
            battle.id = uuid.uuid4()
            return battle

        battle_repo.create.side_effect = create_battle_mock

        # Execute
        battles = await battle_service.generate_finals_battles(category_id)

        # Verify: 1 battle with all winners
        assert len(battles) == 1
        assert len(battles[0].performers) == 3
        assert set(battles[0].performers) == set(winners)
        assert battles[0].phase == BattlePhase.FINALS
        assert battles[0].status == BattleStatus.PENDING
        assert battles[0].outcome_type == BattleOutcomeType.WIN_LOSS

    async def test_no_winners_raises_error(
        self, battle_service, performer_repo, category_id
    ):
        """Test that no pool winners raises ValidationError."""
        performer_repo.get_pool_winners = AsyncMock(return_value=[])

        with pytest.raises(ValidationError, match="no pool winners"):
            await battle_service.generate_finals_battles(category_id)

    async def test_only_one_winner_raises_error(
        self, battle_service, performer_repo, tournament_id, category_id
    ):
        """Test that only one winner raises ValidationError."""
        winner = [create_performer(tournament_id, category_id, "Winner1")]
        performer_repo.get_pool_winners = AsyncMock(return_value=winner)

        with pytest.raises(ValidationError, match="need at least 2 pool winners"):
            await battle_service.generate_finals_battles(category_id)


class TestStartBattle:
    """Tests for battle start operation."""

    async def test_start_battle_success(
        self, battle_service, battle_repo, category_id
    ):
        """Test successfully starting a pending battle."""
        battle_id = uuid.uuid4()
        battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.PENDING,
            BattleOutcomeType.SCORED,
        )
        battle.id = battle_id

        battle_repo.get_by_id.return_value = battle
        battle_repo.get_active_battle.return_value = None  # No active battle

        def update_mock(battle_id, **kwargs):
            battle.status = kwargs.get('status', battle.status)
            return battle

        battle_repo.update.side_effect = update_mock

        # Execute
        result = await battle_service.start_battle(battle_id)

        # Verify
        assert result.status == BattleStatus.ACTIVE
        battle_repo.update.assert_called_once()

    async def test_start_battle_not_found(self, battle_service, battle_repo):
        """Test starting non-existent battle raises error."""
        battle_id = uuid.uuid4()
        battle_repo.get_by_id.return_value = None

        with pytest.raises(ValidationError, match="Battle .* not found"):
            await battle_service.start_battle(battle_id)

    async def test_start_battle_not_pending(
        self, battle_service, battle_repo, category_id
    ):
        """Test starting non-pending battle raises error."""
        battle_id = uuid.uuid4()
        battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.ACTIVE,  # Already active
            BattleOutcomeType.SCORED,
        )
        battle.id = battle_id

        battle_repo.get_by_id.return_value = battle

        with pytest.raises(ValidationError, match="must be PENDING"):
            await battle_service.start_battle(battle_id)

    async def test_start_battle_another_active(
        self, battle_service, battle_repo, category_id
    ):
        """Test starting battle when another is active raises error."""
        battle_id = uuid.uuid4()
        battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.PENDING,
            BattleOutcomeType.SCORED,
        )
        battle.id = battle_id

        other_battle_id = uuid.uuid4()
        active_battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.ACTIVE,
            BattleOutcomeType.SCORED,
        )
        active_battle.id = other_battle_id

        battle_repo.get_by_id.return_value = battle
        battle_repo.get_active_battle.return_value = active_battle

        with pytest.raises(ValidationError, match="another battle .* is already active"):
            await battle_service.start_battle(battle_id)


class TestCompleteBattle:
    """Tests for battle completion operation."""

    async def test_complete_battle_success(
        self, battle_service, battle_repo, category_id
    ):
        """Test successfully completing an active battle."""
        battle_id = uuid.uuid4()
        battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.ACTIVE,
            BattleOutcomeType.SCORED,
        )
        battle.id = battle_id
        battle.outcome = {"winner_id": str(uuid.uuid4())}  # Has outcome

        battle_repo.get_by_id.return_value = battle

        def update_mock(battle_id, **kwargs):
            battle.status = kwargs.get('status', battle.status)
            return battle

        battle_repo.update.side_effect = update_mock

        # Execute
        result = await battle_service.complete_battle(battle_id)

        # Verify
        assert result.status == BattleStatus.COMPLETED
        battle_repo.update.assert_called_once()

    async def test_complete_battle_not_found(self, battle_service, battle_repo):
        """Test completing non-existent battle raises error."""
        battle_id = uuid.uuid4()
        battle_repo.get_by_id.return_value = None

        with pytest.raises(ValidationError, match="Battle .* not found"):
            await battle_service.complete_battle(battle_id)

    async def test_complete_battle_not_active(
        self, battle_service, battle_repo, category_id
    ):
        """Test completing non-active battle raises error."""
        battle_id = uuid.uuid4()
        battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.PENDING,  # Not active
            BattleOutcomeType.SCORED,
        )
        battle.id = battle_id

        battle_repo.get_by_id.return_value = battle

        with pytest.raises(ValidationError, match="must be ACTIVE"):
            await battle_service.complete_battle(battle_id)

    async def test_complete_battle_no_outcome(
        self, battle_service, battle_repo, category_id
    ):
        """Test completing battle without outcome raises error."""
        battle_id = uuid.uuid4()
        battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.ACTIVE,
            BattleOutcomeType.SCORED,
        )
        battle.id = battle_id
        battle.outcome = None  # No outcome

        battle_repo.get_by_id.return_value = battle

        with pytest.raises(ValidationError, match="outcome data is missing"):
            await battle_service.complete_battle(battle_id)


class TestGetNextPendingBattle:
    """Tests for getting next pending battle."""

    async def test_get_next_pending_battle_success(
        self, battle_service, battle_repo, tournament_id, category_id
    ):
        """Test getting next pending battle."""
        battles = [
            create_battle(
                category_id,
                BattlePhase.PRESELECTION,
                BattleStatus.PENDING,
                BattleOutcomeType.SCORED,
            )
            for _ in range(3)
        ]

        battle_repo.get_by_tournament_and_status = AsyncMock(return_value=battles)

        # Execute
        result = await battle_service.get_next_pending_battle(tournament_id)

        # Verify: returns first battle (FIFO)
        assert result == battles[0]
        battle_repo.get_by_tournament_and_status.assert_called_once_with(
            tournament_id, BattleStatus.PENDING
        )

    async def test_get_next_pending_battle_none(
        self, battle_service, battle_repo, tournament_id
    ):
        """Test getting next pending battle when none exist."""
        battle_repo.get_by_tournament_and_status = AsyncMock(return_value=[])

        result = await battle_service.get_next_pending_battle(tournament_id)

        assert result is None


class TestGetActiveBattle:
    """Tests for getting active battle."""

    async def test_get_active_battle_with_tournament_id(
        self, battle_service, battle_repo, tournament_id, category_id
    ):
        """Test getting active battle filtered by tournament."""
        active_battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.ACTIVE,
            BattleOutcomeType.SCORED,
        )

        battle_repo.get_by_tournament_and_status = AsyncMock(return_value=[active_battle])

        # Execute
        result = await battle_service.get_active_battle(tournament_id)

        # Verify
        assert result == active_battle
        battle_repo.get_by_tournament_and_status.assert_called_once_with(
            tournament_id, BattleStatus.ACTIVE
        )

    async def test_get_active_battle_without_tournament_id(
        self, battle_service, battle_repo, category_id
    ):
        """Test getting active battle without tournament filter."""
        active_battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.ACTIVE,
            BattleOutcomeType.SCORED,
        )

        battle_repo.get_active_battle.return_value = active_battle

        # Execute
        result = await battle_service.get_active_battle()

        # Verify
        assert result == active_battle
        battle_repo.get_active_battle.assert_called_once()

    async def test_get_active_battle_none(self, battle_service, battle_repo):
        """Test getting active battle when none exist."""
        battle_repo.get_active_battle.return_value = None

        result = await battle_service.get_active_battle()

        assert result is None


class TestGetBattleQueue:
    """Tests for getting battle queue."""

    async def test_get_battle_queue(
        self, battle_service, battle_repo, tournament_id, category_id
    ):
        """Test getting battle queue organized by status."""
        # Create battles with different statuses
        pending_battles = [
            create_battle(
                category_id,
                BattlePhase.PRESELECTION,
                BattleStatus.PENDING,
                BattleOutcomeType.SCORED,
            )
            for _ in range(3)
        ]

        active_battle = create_battle(
            category_id,
            BattlePhase.PRESELECTION,
            BattleStatus.ACTIVE,
            BattleOutcomeType.SCORED,
        )

        completed_battles = [
            create_battle(
                category_id,
                BattlePhase.PRESELECTION,
                BattleStatus.COMPLETED,
                BattleOutcomeType.SCORED,
            )
            for _ in range(2)
        ]

        all_battles = pending_battles + [active_battle] + completed_battles
        battle_repo.get_by_tournament = AsyncMock(return_value=all_battles)

        # Execute
        queue = await battle_service.get_battle_queue(tournament_id)

        # Verify
        assert len(queue[BattleStatus.PENDING]) == 3
        assert len(queue[BattleStatus.ACTIVE]) == 1
        assert len(queue[BattleStatus.COMPLETED]) == 2
        assert queue[BattleStatus.ACTIVE][0] == active_battle

    async def test_get_battle_queue_empty(
        self, battle_service, battle_repo, tournament_id
    ):
        """Test getting empty battle queue."""
        battle_repo.get_by_tournament = AsyncMock(return_value=[])

        queue = await battle_service.get_battle_queue(tournament_id)

        assert queue[BattleStatus.PENDING] == []
        assert queue[BattleStatus.ACTIVE] == []
        assert queue[BattleStatus.COMPLETED] == []
