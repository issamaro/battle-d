"""Tests for PoolService.

Tests pool creation, distribution, and winner determination.
See: ROADMAP.md §2.2 Pool Distribution Service
"""
import pytest
import uuid
from typing import List
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.exceptions import ValidationError
from app.models.pool import Pool
from app.models.performer import Performer
from app.repositories.pool import PoolRepository
from app.repositories.performer import PerformerRepository
from app.services.pool_service import PoolService


@pytest.fixture
def pool_repo():
    """Mock pool repository."""
    return AsyncMock(spec=PoolRepository)


@pytest.fixture
def performer_repo():
    """Mock performer repository."""
    return AsyncMock(spec=PerformerRepository)


@pytest.fixture
def pool_service(pool_repo, performer_repo):
    """Pool service with mocked repositories."""
    return PoolService(pool_repo, performer_repo)


@pytest.fixture
def tournament_id():
    """Sample tournament UUID."""
    return uuid.uuid4()


@pytest.fixture
def category_id():
    """Sample category UUID."""
    return uuid.uuid4()


def create_performer_with_score(
    tournament_id: uuid.UUID,
    category_id: uuid.UUID,
    score: Decimal,
    name: str = "Performer",
) -> Performer:
    """Helper to create a performer with preselection score."""
    performer = Performer(
        tournament_id=tournament_id,
        category_id=category_id,
        dancer_id=uuid.uuid4(),
        preselection_score=score,
    )
    performer.id = uuid.uuid4()
    return performer


def create_performer_with_points(
    tournament_id: uuid.UUID,
    category_id: uuid.UUID,
    wins: int = 0,
    draws: int = 0,
    losses: int = 0,
) -> Performer:
    """Helper to create a performer with pool stats."""
    performer = Performer(
        tournament_id=tournament_id,
        category_id=category_id,
        dancer_id=uuid.uuid4(),
        pool_wins=wins,
        pool_draws=draws,
        pool_losses=losses,
    )
    performer.id = uuid.uuid4()
    return performer


def create_pool(category_id: uuid.UUID, name: str) -> Pool:
    """Helper to create a pool."""
    pool = Pool(category_id=category_id, name=name)
    pool.id = uuid.uuid4()
    pool.performers = []
    return pool


class TestCreatePoolsFromPreselection:
    """Tests for pool creation from preselection results."""

    async def test_create_pools_success(
        self,
        pool_service,
        performer_repo,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test successful pool creation with 8 performers, groups_ideal=2.

        BR-POOL-001: Equal pool sizes required.
        8 performers, 2 pools:
        - Ideal capacity = 2×4 = 8, but registered (8) < ideal + 1 (9)
        - Reduce: 2×4=8 NOT < 8, 2×3=6 < 8 ✓
        - Result: 6 qualify (2 pools × 3 each), 2 eliminated
        """
        # Setup: 8 performers with scores
        performers = [
            create_performer_with_score(
                tournament_id, category_id, Decimal(f"{10 - i}.0"), f"P{i}"
            )
            for i in range(8)
        ]
        performer_repo.get_by_category.return_value = performers

        # Mock pool creation
        def create_pool_mock(pool):
            pool.id = uuid.uuid4()
            return pool

        pool_repo.create.side_effect = create_pool_mock

        # Execute: create 2 pools
        pools = await pool_service.create_pools_from_preselection(category_id, 2)

        # Verify: 2 pools created (8 registered → 6 qualify → 2 pools of 3 each)
        assert len(pools) == 2
        assert pools[0].name == "Pool A"
        assert pools[1].name == "Pool B"

        # BR-POOL-001: Equal pool sizes
        assert len(pools[0].performers) == 3
        assert len(pools[1].performers) == 3

        # Verify qualified performers (top 6 by score)
        all_pool_performers = []
        for pool in pools:
            all_pool_performers.extend(pool.performers)
        assert len(all_pool_performers) == 6

        # Top 6 performers should be qualified (scores 10.0 → 5.0)
        qualified_scores = [p.preselection_score for p in all_pool_performers]
        assert all(score >= Decimal("5.0") for score in qualified_scores)

    async def test_create_pools_even_distribution(
        self,
        pool_service,
        performer_repo,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test even distribution: 10 performers → 8 qualify → 2 pools of 4 each.

        BR-POOL-001: Equal pool sizes.
        10 performers, 2 pools:
        - Ideal capacity = 2×4 = 8, registered (10) >= ideal + 1 (9) ✓
        - Use ideal capacity: 8 qualify, 2 eliminated
        - Result: 2 pools × 4 each
        """
        performers = [
            create_performer_with_score(
                tournament_id, category_id, Decimal(f"{10 - i}.0")
            )
            for i in range(10)
        ]
        performer_repo.get_by_category.return_value = performers

        def create_pool_mock(pool):
            pool.id = uuid.uuid4()
            return pool

        pool_repo.create.side_effect = create_pool_mock

        pools = await pool_service.create_pools_from_preselection(category_id, 2)

        # Verify BR-POOL-001: equal distribution
        assert len(pools) == 2
        assert len(pools[0].performers) == 4
        assert len(pools[1].performers) == 4

    async def test_create_pools_equal_distribution_11_performers(
        self,
        pool_service,
        performer_repo,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test BR-POOL-001: 11 performers → equal pools.

        11 performers, 2 pools:
        - Ideal capacity = 2×4 = 8, registered (11) >= ideal + 1 (9) ✓
        - Use ideal capacity: 8 qualify, 3 eliminated
        - Result: 2 pools × 4 each (equal sizes, not 5+4)
        """
        performers = [
            create_performer_with_score(
                tournament_id, category_id, Decimal(f"{10 - i}.0")
            )
            for i in range(11)
        ]
        performer_repo.get_by_category.return_value = performers

        def create_pool_mock(pool):
            pool.id = uuid.uuid4()
            return pool

        pool_repo.create.side_effect = create_pool_mock

        pools = await pool_service.create_pools_from_preselection(category_id, 2)

        # BR-POOL-001: Equal distribution (4 + 4 = 8, not 5 + 4)
        assert len(pools) == 2
        assert len(pools[0].performers) == 4
        assert len(pools[1].performers) == 4

    async def test_create_pools_no_performers(
        self, pool_service, performer_repo, category_id
    ):
        """Test that no performers raises ValidationError."""
        performer_repo.get_by_category.return_value = []

        with pytest.raises(ValidationError, match="no performers in category"):
            await pool_service.create_pools_from_preselection(category_id, 2)

    async def test_create_pools_missing_scores(
        self,
        pool_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test that missing preselection scores raises ValidationError."""
        performers = [
            create_performer_with_score(tournament_id, category_id, None)  # type: ignore
            for _ in range(5)
        ]
        performer_repo.get_by_category.return_value = performers

        with pytest.raises(ValidationError, match="missing preselection scores"):
            await pool_service.create_pools_from_preselection(category_id, 2)

    async def test_create_pools_insufficient_performers(
        self,
        pool_service,
        performer_repo,
        tournament_id,
        category_id,
    ):
        """Test that too few performers raises ValidationError."""
        # Only 4 performers, but minimum is (2 * 2) + 1 = 5
        performers = [
            create_performer_with_score(tournament_id, category_id, Decimal("10.0"))
            for _ in range(4)
        ]
        performer_repo.get_by_category.return_value = performers

        with pytest.raises(ValidationError):
            await pool_service.create_pools_from_preselection(category_id, 2)


class TestGetPoolWinners:
    """Tests for pool winner determination."""

    async def test_get_pool_winners_single_winner_per_pool(
        self,
        pool_service,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test getting pool winners when each pool has clear winner."""
        # Pool A: P1 has 9 points (3 wins), P2 has 6, P3 has 3
        pool_a = create_pool(category_id, "Pool A")
        pool_a.performers = [
            create_performer_with_points(tournament_id, category_id, wins=3),  # 9 pts
            create_performer_with_points(
                tournament_id, category_id, wins=2, draws=0
            ),  # 6 pts
            create_performer_with_points(
                tournament_id, category_id, wins=1, draws=0
            ),  # 3 pts
        ]

        # Pool B: P1 has 10 points (3 wins + 1 draw)
        pool_b = create_pool(category_id, "Pool B")
        pool_b.performers = [
            create_performer_with_points(
                tournament_id, category_id, wins=3, draws=1
            ),  # 10 pts
            create_performer_with_points(
                tournament_id, category_id, wins=2, draws=1
            ),  # 7 pts
            create_performer_with_points(
                tournament_id, category_id, wins=1, draws=0
            ),  # 3 pts
        ]

        pool_repo.get_by_category.return_value = [pool_a, pool_b]
        pool_repo.update.side_effect = lambda p: p

        # Execute
        winners = await pool_service.get_pool_winners(category_id)

        # Verify: 2 winners (one from each pool)
        assert len(winners) == 2
        assert winners[0].pool_points == 9
        assert winners[1].pool_points == 10

        # Verify winner_id was set on pools
        assert pool_repo.update.call_count == 2

    async def test_get_pool_winners_with_tie(
        self,
        pool_service,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test getting pool winners when there's a tie."""
        # Pool A: P1 and P2 both have 9 points (3 wins each)
        pool_a = create_pool(category_id, "Pool A")
        pool_a.performers = [
            create_performer_with_points(tournament_id, category_id, wins=3),  # 9 pts
            create_performer_with_points(tournament_id, category_id, wins=3),  # 9 pts
            create_performer_with_points(
                tournament_id, category_id, wins=1, draws=0
            ),  # 3 pts
        ]

        pool_repo.get_by_category.return_value = [pool_a]

        # Execute
        winners = await pool_service.get_pool_winners(category_id)

        # Verify: 2 winners returned (both tied)
        assert len(winners) == 2
        assert all(w.pool_points == 9 for w in winners)

        # Verify winner_id was NOT set (tie unresolved)
        pool_repo.update.assert_not_called()

    async def test_get_pool_winners_no_pools(
        self, pool_service, pool_repo, category_id
    ):
        """Test that no pools raises ValidationError."""
        pool_repo.get_by_category.return_value = []

        with pytest.raises(ValidationError, match="no pools found"):
            await pool_service.get_pool_winners(category_id)

    async def test_get_pool_winners_empty_pool(
        self, pool_service, pool_repo, category_id
    ):
        """Test that empty pool raises ValidationError."""
        pool_a = create_pool(category_id, "Pool A")
        pool_a.performers = []  # Empty pool

        pool_repo.get_by_category.return_value = [pool_a]

        with pytest.raises(ValidationError, match="has no performers"):
            await pool_service.get_pool_winners(category_id)


class TestCheckForTies:
    """Tests for tie detection."""

    async def test_check_for_ties_no_ties(
        self,
        pool_service,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test tie check when no ties exist."""
        pool_a = create_pool(category_id, "Pool A")
        pool_a.performers = [
            create_performer_with_points(tournament_id, category_id, wins=3),  # 9 pts
            create_performer_with_points(tournament_id, category_id, wins=2),  # 6 pts
        ]

        pool_repo.get_by_category.return_value = [pool_a]

        ties = await pool_service.check_for_ties(category_id)

        assert ties == {}

    async def test_check_for_ties_with_ties(
        self,
        pool_service,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test tie detection when ties exist."""
        pool_a = create_pool(category_id, "Pool A")
        pool_a.id = uuid.uuid4()
        p1 = create_performer_with_points(tournament_id, category_id, wins=3)  # 9 pts
        p2 = create_performer_with_points(tournament_id, category_id, wins=3)  # 9 pts
        pool_a.performers = [p1, p2]

        pool_repo.get_by_category.return_value = [pool_a]

        ties = await pool_service.check_for_ties(category_id)

        assert pool_a.id in ties
        assert len(ties[pool_a.id]) == 2
        assert p1 in ties[pool_a.id]
        assert p2 in ties[pool_a.id]


class TestSetPoolWinner:
    """Tests for setting pool winner."""

    async def test_set_pool_winner_success(
        self,
        pool_service,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test successfully setting pool winner."""
        pool_id = uuid.uuid4()
        winner_id = uuid.uuid4()

        pool = create_pool(category_id, "Pool A")
        pool.id = pool_id
        performer = create_performer_with_points(tournament_id, category_id, wins=3)
        performer.id = winner_id
        pool.performers = [performer]

        pool_repo.get_by_id.return_value = pool
        pool_repo.update.side_effect = lambda p: p

        result = await pool_service.set_pool_winner(pool_id, winner_id)

        assert result.winner_id == winner_id
        pool_repo.update.assert_called_once()

    async def test_set_pool_winner_pool_not_found(
        self, pool_service, pool_repo
    ):
        """Test setting winner on non-existent pool."""
        pool_id = uuid.uuid4()
        winner_id = uuid.uuid4()

        pool_repo.get_by_id.return_value = None

        with pytest.raises(ValidationError, match="not found"):
            await pool_service.set_pool_winner(pool_id, winner_id)

    async def test_set_pool_winner_not_in_pool(
        self,
        pool_service,
        pool_repo,
        tournament_id,
        category_id,
    ):
        """Test setting winner who is not in the pool."""
        pool_id = uuid.uuid4()
        winner_id = uuid.uuid4()
        other_id = uuid.uuid4()

        pool = create_pool(category_id, "Pool A")
        pool.id = pool_id
        performer = create_performer_with_points(tournament_id, category_id, wins=3)
        performer.id = other_id  # Different ID
        pool.performers = [performer]

        pool_repo.get_by_id.return_value = pool

        with pytest.raises(ValidationError, match="is not in pool"):
            await pool_service.set_pool_winner(pool_id, winner_id)


class TestGetPoolWithPerformers:
    """Tests for get_pool_with_performers."""

    async def test_get_pool_with_performers_success(
        self,
        pool_service,
        pool_repo,
        category_id,
    ):
        """Test getting pool with performers."""
        pool_id = uuid.uuid4()
        pool = create_pool(category_id, "Pool A")
        pool.id = pool_id

        pool_repo.get_by_id.return_value = pool

        result = await pool_service.get_pool_with_performers(pool_id)

        assert result == pool
        pool_repo.get_by_id.assert_called_once_with(pool_id)

    async def test_get_pool_with_performers_not_found(
        self, pool_service, pool_repo
    ):
        """Test getting non-existent pool."""
        pool_id = uuid.uuid4()
        pool_repo.get_by_id.return_value = None

        result = await pool_service.get_pool_with_performers(pool_id)

        assert result is None
