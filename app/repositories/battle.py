"""Battle repository."""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.battle import Battle, BattlePhase, BattleStatus, BattleOutcomeType
from app.repositories.base import BaseRepository


class BattleRepository(BaseRepository[Battle]):
    """Repository for Battle model."""

    def __init__(self, session: AsyncSession):
        """Initialize BattleRepository.

        Args:
            session: Database session
        """
        super().__init__(Battle, session)

    async def get_by_category(self, category_id: uuid.UUID) -> List[Battle]:
        """Get all battles in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of battles in the category
        """
        result = await self.session.execute(
            select(Battle)
            .options(selectinload(Battle.performers))
            .where(Battle.category_id == category_id)
        )
        return list(result.scalars().all())

    async def get_by_phase(
        self, category_id: uuid.UUID, phase: BattlePhase
    ) -> List[Battle]:
        """Get battles by phase for a category.

        Args:
            category_id: Category UUID
            phase: Battle phase

        Returns:
            List of battles in the given phase
        """
        result = await self.session.execute(
            select(Battle)
            .options(selectinload(Battle.performers))
            .where(
                Battle.category_id == category_id,
                Battle.phase == phase,
            )
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: BattleStatus) -> List[Battle]:
        """Get battles by status (across all categories).

        Args:
            status: Battle status

        Returns:
            List of battles with the given status
        """
        result = await self.session.execute(
            select(Battle)
            .options(selectinload(Battle.performers))
            .where(Battle.status == status)
        )
        return list(result.scalars().all())

    async def get_active_battle(self) -> Optional[Battle]:
        """Get the currently active battle (if any).

        Returns:
            Active battle or None if no battle is active
        """
        result = await self.session.execute(
            select(Battle)
            .options(selectinload(Battle.performers))
            .where(Battle.status == BattleStatus.ACTIVE)
        )
        return result.scalar_one_or_none()

    async def get_with_performers(self, id: uuid.UUID) -> Optional[Battle]:
        """Get battle with performers loaded.

        Args:
            id: Battle UUID

        Returns:
            Battle with performers or None if not found
        """
        result = await self.session.execute(
            select(Battle)
            .options(selectinload(Battle.performers))
            .where(Battle.id == id)
        )
        return result.scalar_one_or_none()

    async def create_battle(
        self,
        category_id: uuid.UUID,
        phase: BattlePhase,
        outcome_type: BattleOutcomeType,
        performer_ids: List[uuid.UUID],
    ) -> Battle:
        """Create a new battle.

        Args:
            category_id: Category UUID
            phase: Battle phase
            outcome_type: Type of outcome
            performer_ids: List of performer UUIDs in this battle

        Returns:
            Created battle instance
        """
        # Create the battle
        battle = await self.create(
            category_id=category_id,
            phase=phase,
            status=BattleStatus.PENDING,
            outcome_type=outcome_type,
        )

        # Add performers (need to load them from DB)
        from app.models.performer import Performer

        for performer_id in performer_ids:
            result = await self.session.execute(
                select(Performer).where(Performer.id == performer_id)
            )
            performer = result.scalar_one()
            battle.performers.append(performer)

        await self.session.flush()
        await self.session.refresh(battle)
        return battle

    async def get_by_tournament(self, tournament_id: uuid.UUID) -> List[Battle]:
        """Get all battles for a tournament.

        Args:
            tournament_id: Tournament UUID

        Returns:
            List of battles in the tournament
        """
        # Import here to avoid circular dependency
        from app.models.category import Category

        result = await self.session.execute(
            select(Battle)
            .join(Category, Battle.category_id == Category.id)
            .options(selectinload(Battle.performers))
            .where(Category.tournament_id == tournament_id)
        )
        return list(result.scalars().all())

    async def get_by_tournament_and_status(
        self, tournament_id: uuid.UUID, status: BattleStatus
    ) -> List[Battle]:
        """Get battles by tournament and status.

        Args:
            tournament_id: Tournament UUID
            status: Battle status

        Returns:
            List of battles matching criteria
        """
        # Import here to avoid circular dependency
        from app.models.category import Category

        result = await self.session.execute(
            select(Battle)
            .join(Category, Battle.category_id == Category.id)
            .options(selectinload(Battle.performers))
            .where(
                Category.tournament_id == tournament_id,
                Battle.status == status,
            )
        )
        return list(result.scalars().all())
