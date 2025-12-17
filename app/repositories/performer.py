"""Performer repository."""
import uuid
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.performer import Performer
from app.repositories.base import BaseRepository


class PerformerRepository(BaseRepository[Performer]):
    """Repository for Performer model."""

    def __init__(self, session: AsyncSession):
        """Initialize PerformerRepository.

        Args:
            session: Database session
        """
        super().__init__(Performer, session)

    async def get_by_tournament(self, tournament_id: uuid.UUID) -> List[Performer]:
        """Get all performers in a tournament.

        Args:
            tournament_id: Tournament UUID

        Returns:
            List of performers in the tournament
        """
        result = await self.session.execute(
            select(Performer).where(Performer.tournament_id == tournament_id)
        )
        return list(result.scalars().all())

    async def get_by_category(self, category_id: uuid.UUID) -> List[Performer]:
        """Get all performers in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of performers in the category
        """
        result = await self.session.execute(
            select(Performer)
            .options(selectinload(Performer.dancer))
            .where(Performer.category_id == category_id)
        )
        return list(result.scalars().all())

    async def get_by_category_with_partners(
        self, category_id: uuid.UUID
    ) -> List[Performer]:
        """Get all performers in a category with duo partner relationships loaded.

        Args:
            category_id: Category UUID

        Returns:
            List of performers in the category with partner data
        """
        result = await self.session.execute(
            select(Performer)
            .options(
                selectinload(Performer.dancer),
                selectinload(Performer.duo_partner).selectinload(Performer.dancer),
            )
            .where(Performer.category_id == category_id)
        )
        return list(result.scalars().all())

    async def get_with_dancer(self, id: uuid.UUID) -> Optional[Performer]:
        """Get performer with dancer data loaded.

        Args:
            id: Performer UUID

        Returns:
            Performer with dancer or None if not found
        """
        result = await self.session.execute(
            select(Performer)
            .options(selectinload(Performer.dancer))
            .where(Performer.id == id)
        )
        return result.scalar_one_or_none()

    async def dancer_registered_in_tournament(
        self, dancer_id: uuid.UUID, tournament_id: uuid.UUID
    ) -> bool:
        """Check if dancer is already registered in tournament.

        Args:
            dancer_id: Dancer UUID
            tournament_id: Tournament UUID

        Returns:
            True if already registered, False otherwise
        """
        result = await self.session.execute(
            select(Performer.id).where(
                Performer.dancer_id == dancer_id,
                Performer.tournament_id == tournament_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_performer(
        self,
        tournament_id: uuid.UUID,
        category_id: uuid.UUID,
        dancer_id: uuid.UUID,
        duo_partner_id: Optional[uuid.UUID] = None,
    ) -> Performer:
        """Create a new performer registration.

        Args:
            tournament_id: Tournament UUID
            category_id: Category UUID
            dancer_id: Dancer UUID
            duo_partner_id: Partner performer UUID (for 2v2 categories)

        Returns:
            Created performer instance
        """
        return await self.create(
            tournament_id=tournament_id,
            category_id=category_id,
            dancer_id=dancer_id,
            duo_partner_id=duo_partner_id,
        )

    async def get_top_by_preselection_score(
        self, category_id: uuid.UUID, limit: int
    ) -> List[Performer]:
        """Get top performers by preselection score.

        Args:
            category_id: Category UUID
            limit: Number of performers to return

        Returns:
            List of top-scoring performers
        """
        result = await self.session.execute(
            select(Performer)
            .where(
                Performer.category_id == category_id,
                Performer.preselection_score.isnot(None),
            )
            .order_by(Performer.preselection_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_pool_points(
        self, category_id: uuid.UUID
    ) -> List[Performer]:
        """Get performers ordered by pool points.

        Args:
            category_id: Category UUID

        Returns:
            List of performers ordered by pool points (descending)
        """
        performers = await self.get_by_category(category_id)
        # Sort by pool_points property (computed in Python)
        return sorted(performers, key=lambda p: p.pool_points, reverse=True)

    async def link_duo_partners(
        self, performer1_id: uuid.UUID, performer2_id: uuid.UUID
    ) -> None:
        """Link two performers as duo partners.

        Args:
            performer1_id: First performer UUID
            performer2_id: Second performer UUID
        """
        # Get both performers
        performer1 = await self.get_by_id(performer1_id)
        performer2 = await self.get_by_id(performer2_id)

        if not performer1 or not performer2:
            raise ValueError("One or both performers not found")

        # Update duo_partner_id for both
        performer1.duo_partner_id = performer2_id
        performer2.duo_partner_id = performer1_id

        # Commit changes
        await self.session.commit()

    async def get_pool_with_performers(self, pool_id: uuid.UUID):
        """Get a pool with its performers loaded.

        This is a convenience method that delegates to PoolRepository.
        Kept for backwards compatibility with BattleService.

        Args:
            pool_id: Pool UUID

        Returns:
            Pool with performers or None if not found

        Note:
            This method requires access to PoolRepository.
            In practice, this should be called from PoolService instead.
        """
        # Import here to avoid circular dependency
        from app.models.pool import Pool

        result = await self.session.execute(
            select(Pool)
            .options(selectinload(Pool.performers))
            .where(Pool.id == pool_id)
        )
        return result.scalar_one_or_none()

    async def get_pool_winners(self, category_id: uuid.UUID) -> List[Performer]:
        """Get pool winners for a category.

        Returns performers who are marked as winners in their pools.

        Args:
            category_id: Category UUID

        Returns:
            List of performers who are pool winners

        Note:
            This only returns performers where pool.winner_id is set.
            Does not calculate winners - that's done by PoolService.
        """
        # Import here to avoid circular dependency
        from app.models.pool import Pool

        result = await self.session.execute(
            select(Performer)
            .join(Pool, Pool.winner_id == Performer.id)
            .where(Pool.category_id == category_id)
        )
        return list(result.scalars().all())

    # ========== Guest Performer Methods ==========

    async def get_guest_count(self, category_id: uuid.UUID) -> int:
        """Get count of guest performers in a category.

        Args:
            category_id: Category UUID

        Returns:
            Number of guest performers
        """
        result = await self.session.execute(
            select(func.count(Performer.id)).where(
                Performer.category_id == category_id,
                Performer.is_guest == True,
            )
        )
        return result.scalar_one()

    async def get_regular_performers(
        self, category_id: uuid.UUID
    ) -> List[Performer]:
        """Get non-guest performers in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of regular (non-guest) performers
        """
        result = await self.session.execute(
            select(Performer)
            .options(selectinload(Performer.dancer))
            .where(
                Performer.category_id == category_id,
                Performer.is_guest == False,
            )
        )
        return list(result.scalars().all())

    async def get_guests(self, category_id: uuid.UUID) -> List[Performer]:
        """Get guest performers in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of guest performers
        """
        result = await self.session.execute(
            select(Performer)
            .options(selectinload(Performer.dancer))
            .where(
                Performer.category_id == category_id,
                Performer.is_guest == True,
            )
        )
        return list(result.scalars().all())

    async def create_guest_performer(
        self,
        tournament_id: uuid.UUID,
        category_id: uuid.UUID,
        dancer_id: uuid.UUID,
    ) -> Performer:
        """Create a guest performer with automatic top score.

        Guest performers skip preselection and are guaranteed to qualify
        for pools with the maximum preselection score (10.0).

        Args:
            tournament_id: Tournament UUID
            category_id: Category UUID
            dancer_id: Dancer UUID

        Returns:
            Created guest performer with preselection_score=10.0
        """
        return await self.create(
            tournament_id=tournament_id,
            category_id=category_id,
            dancer_id=dancer_id,
            is_guest=True,
            preselection_score=Decimal("10.00"),
        )

    async def convert_to_guest(self, performer_id: uuid.UUID) -> Performer:
        """Convert a regular performer to guest.

        Sets is_guest=True and preselection_score=10.0.

        Args:
            performer_id: Performer UUID

        Returns:
            Updated performer with guest status

        Raises:
            ValueError: If performer not found
        """
        performer = await self.get_by_id(performer_id)
        if not performer:
            raise ValueError(f"Performer {performer_id} not found")

        performer.is_guest = True
        performer.preselection_score = Decimal("10.00")
        await self.session.commit()
        return performer
