"""Pool repository."""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pool import Pool
from app.repositories.base import BaseRepository


class PoolRepository(BaseRepository[Pool]):
    """Repository for Pool model."""

    def __init__(self, session: AsyncSession):
        """Initialize PoolRepository.

        Args:
            session: Database session
        """
        super().__init__(Pool, session)

    async def get_by_category(self, category_id: uuid.UUID) -> List[Pool]:
        """Get all pools in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of pools in the category
        """
        result = await self.session.execute(
            select(Pool)
            .options(selectinload(Pool.performers))
            .where(Pool.category_id == category_id)
        )
        return list(result.scalars().all())

    async def get_with_performers(self, id: uuid.UUID) -> Optional[Pool]:
        """Get pool with performers loaded.

        Args:
            id: Pool UUID

        Returns:
            Pool with performers or None if not found
        """
        result = await self.session.execute(
            select(Pool)
            .options(selectinload(Pool.performers))
            .where(Pool.id == id)
        )
        return result.scalar_one_or_none()

    async def create_pool(
        self,
        category_id: uuid.UUID,
        name: str,
    ) -> Pool:
        """Create a new pool.

        Args:
            category_id: Category UUID
            name: Pool name (e.g., "Pool A")

        Returns:
            Created pool instance
        """
        return await self.create(
            category_id=category_id,
            name=name,
        )
