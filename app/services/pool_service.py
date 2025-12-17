"""Pool service for pool creation and winner determination.

See: ROADMAP.md §2.2 Pool Distribution Service
"""
import uuid
from typing import List, Optional
from decimal import Decimal

from app.exceptions import ValidationError
from app.models.pool import Pool
from app.models.performer import Performer
from app.repositories.pool import PoolRepository
from app.repositories.performer import PerformerRepository
from app.utils.tournament_calculations import (
    calculate_pool_capacity,
    distribute_performers_to_pools,
)


class PoolService:
    """Service for pool creation and winner determination.

    Handles:
    - Pool creation from preselection results
    - Performer distribution across pools
    - Pool winner determination based on pool_points
    - Tie detection for winner selection

    See: DOMAIN_MODEL.md §Pool for business rules
    """

    def __init__(
        self, pool_repo: PoolRepository, performer_repo: PerformerRepository
    ):
        """Initialize pool service.

        Args:
            pool_repo: Pool repository
            performer_repo: Performer repository
        """
        self.pool_repo = pool_repo
        self.performer_repo = performer_repo

    async def create_pools_from_preselection(
        self, category_id: uuid.UUID, groups_ideal: int
    ) -> List[Pool]:
        """Create pools from preselection results.

        Gets all performers in category, sorts by preselection_score (descending),
        selects top performers based on pool capacity calculation, and distributes
        them evenly across pools.

        Args:
            category_id: Category UUID
            groups_ideal: Target number of pools (usually 2)

        Returns:
            List of created pools with assigned performers

        Raises:
            ValidationError: If not enough performers, missing scores, or calculation error
        """
        # Get all performers in category
        performers = await self.performer_repo.get_by_category(category_id)

        if not performers:
            raise ValidationError([f"Cannot create pools: no performers in category {category_id}"])

        # Verify all have preselection scores
        performers_without_scores = [
            p for p in performers if p.preselection_score is None
        ]
        if performers_without_scores:
            raise ValidationError(
                [f"Cannot create pools: {len(performers_without_scores)} performers missing preselection scores"]
            )

        # Calculate pool capacity using BR-POOL-001 rules
        registered_count = len(performers)
        try:
            pool_performers_count, _, eliminated_count = calculate_pool_capacity(
                registered_count, groups_ideal
            )
        except ValueError as e:
            raise ValidationError([str(e)])

        # Sort by preselection score (descending), then guest priority, then registration time
        # BR-GUEST-006: Guests win tiebreak at pool qualification boundary
        sorted_performers = sorted(
            performers,
            key=lambda p: (
                -p.preselection_score,  # Highest score first
                -int(p.is_guest),       # Guests before regulars at same score
                p.created_at,           # Earlier registration wins ties
            ),
        )
        qualified_performers = sorted_performers[:pool_performers_count]

        # Calculate pool distribution
        try:
            pool_sizes = distribute_performers_to_pools(
                pool_performers_count, groups_ideal
            )
        except ValueError as e:
            raise ValidationError([str(e)])

        # Create pools and assign performers
        pools = []
        performer_index = 0

        for pool_num, pool_size in enumerate(pool_sizes, start=1):
            # Create pool
            pool = Pool(
                category_id=category_id,
                name=f"Pool {chr(64 + pool_num)}",  # Pool A, Pool B, etc.
            )
            pool.performers = qualified_performers[
                performer_index : performer_index + pool_size
            ]
            created_pool = await self.pool_repo.create(pool)
            pools.append(created_pool)
            performer_index += pool_size

        return pools

    async def get_pool_winners(self, category_id: uuid.UUID) -> List[Performer]:
        """Get pool winners for a category.

        Finds the performer with the highest pool_points in each pool.
        If there's a tie, returns all tied performers (tiebreak needed).

        Args:
            category_id: Category UUID

        Returns:
            List of pool winners (one per pool, or multiple if tied)

        Raises:
            ValidationError: If no pools found or pools have no performers
        """
        # Get all pools for category
        pools = await self.pool_repo.get_by_category(category_id)

        if not pools:
            raise ValidationError([f"Cannot determine winners: no pools found for category {category_id}"])

        winners = []

        for pool in pools:
            if not pool.performers:
                raise ValidationError(
                    [f"Cannot determine winner: pool {pool.name} has no performers"]
                )

            # Find performers with highest pool_points
            max_points = max(p.pool_points for p in pool.performers)
            pool_winners = [p for p in pool.performers if p.pool_points == max_points]

            # If tie, we return all tied performers (tiebreak service will handle)
            # For now, if there's exactly one winner, we set it on the pool
            if len(pool_winners) == 1:
                pool.winner_id = pool_winners[0].id
                await self.pool_repo.update(pool)
                winners.append(pool_winners[0])
            else:
                # Tie detected - return all tied performers for this pool
                # TiebreakService will create a tiebreak battle
                winners.extend(pool_winners)

        return winners

    async def get_pool_with_performers(self, pool_id: uuid.UUID) -> Optional[Pool]:
        """Get a pool with its performers loaded.

        Args:
            pool_id: Pool UUID

        Returns:
            Pool with performers or None if not found
        """
        pool = await self.pool_repo.get_by_id(pool_id)
        if not pool:
            return None

        # Performers relationship should be loaded via selectinload in repository
        # For now, return the pool (repository handles loading)
        return pool

    async def check_for_ties(
        self, category_id: uuid.UUID
    ) -> dict[uuid.UUID, List[Performer]]:
        """Check for ties in pool winner determination.

        Args:
            category_id: Category UUID

        Returns:
            Dictionary mapping pool_id to list of tied performers
            Empty dict if no ties
        """
        pools = await self.pool_repo.get_by_category(category_id)
        ties = {}

        for pool in pools:
            if not pool.performers:
                continue

            # Find performers with highest pool_points
            max_points = max(p.pool_points for p in pool.performers)
            pool_winners = [p for p in pool.performers if p.pool_points == max_points]

            # If more than one winner, it's a tie
            if len(pool_winners) > 1:
                ties[pool.id] = pool_winners

        return ties

    async def set_pool_winner(
        self, pool_id: uuid.UUID, winner_id: uuid.UUID
    ) -> Pool:
        """Set the winner for a pool.

        Used after tiebreak battle is resolved.

        Args:
            pool_id: Pool UUID
            winner_id: Winner performer UUID

        Returns:
            Updated pool

        Raises:
            ValidationError: If pool not found or winner not in pool
        """
        pool = await self.pool_repo.get_by_id(pool_id)
        if not pool:
            raise ValidationError([f"Pool {pool_id} not found"])

        # Verify winner is in the pool
        performer_ids = [p.id for p in pool.performers]
        if winner_id not in performer_ids:
            raise ValidationError(
                [f"Performer {winner_id} is not in pool {pool.name}"]
            )

        pool.winner_id = winner_id
        updated_pool = await self.pool_repo.update(pool)

        return updated_pool
