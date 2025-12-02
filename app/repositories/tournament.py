"""Tournament repository."""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tournament import Tournament, TournamentStatus, TournamentPhase
from app.repositories.base import BaseRepository


class TournamentRepository(BaseRepository[Tournament]):
    """Repository for Tournament model."""

    def __init__(self, session: AsyncSession):
        """Initialize TournamentRepository.

        Args:
            session: Database session
        """
        super().__init__(Tournament, session)

    async def get_with_categories(self, id: uuid.UUID) -> Optional[Tournament]:
        """Get tournament with categories loaded.

        Args:
            id: Tournament UUID

        Returns:
            Tournament with categories or None if not found
        """
        result = await self.session.execute(
            select(Tournament)
            .options(selectinload(Tournament.categories))
            .where(Tournament.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> Optional[Tournament]:
        """Get the active tournament (only one allowed at a time).

        Returns:
            Active tournament or None if no active tournament

        Note: If multiple ACTIVE tournaments exist (data integrity violation),
        returns the most recently created one.
        """
        result = await self.session.execute(
            select(Tournament)
            .where(Tournament.status == TournamentStatus.ACTIVE)
            .order_by(Tournament.created_at.desc())
        )
        return result.scalars().first()

    async def get_active_tournaments(self) -> List[Tournament]:
        """Get all active tournaments.

        Returns:
            List of active tournaments
        """
        result = await self.session.execute(
            select(Tournament).where(Tournament.status == TournamentStatus.ACTIVE)
        )
        return list(result.scalars().all())

    async def get_by_phase(self, phase: TournamentPhase) -> List[Tournament]:
        """Get tournaments by phase.

        Args:
            phase: Tournament phase

        Returns:
            List of tournaments in the given phase
        """
        result = await self.session.execute(
            select(Tournament).where(Tournament.phase == phase)
        )
        return list(result.scalars().all())

    async def create_tournament(self, name: str) -> Tournament:
        """Create a new tournament.

        Args:
            name: Tournament name

        Returns:
            Created tournament instance (starts in CREATED status)
        """
        return await self.create(
            name=name,
            status=TournamentStatus.CREATED,  # Start in CREATED status
            phase=TournamentPhase.REGISTRATION,
        )
