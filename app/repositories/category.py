"""Category repository."""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category model."""

    def __init__(self, session: AsyncSession):
        """Initialize CategoryRepository.

        Args:
            session: Database session
        """
        super().__init__(Category, session)

    async def get_by_tournament(self, tournament_id: uuid.UUID) -> List[Category]:
        """Get all categories for a tournament.

        Args:
            tournament_id: Tournament UUID

        Returns:
            List of categories in the tournament
        """
        result = await self.session.execute(
            select(Category).where(Category.tournament_id == tournament_id)
        )
        return list(result.scalars().all())

    async def get_with_performers(self, id: uuid.UUID) -> Optional[Category]:
        """Get category with performers loaded.

        Args:
            id: Category UUID

        Returns:
            Category with performers or None if not found
        """
        result = await self.session.execute(
            select(Category)
            .options(selectinload(Category.performers))
            .where(Category.id == id)
        )
        return result.scalar_one_or_none()

    async def create_category(
        self,
        tournament_id: uuid.UUID,
        name: str,
        is_duo: bool = False,
        groups_ideal: int = 2,
        performers_ideal: int = 4,
    ) -> Category:
        """Create a new category.

        Args:
            tournament_id: Tournament UUID
            name: Category name
            is_duo: Whether this is a 2v2 category
            groups_ideal: Target number of pools
            performers_ideal: Target performers per pool

        Returns:
            Created category instance
        """
        return await self.create(
            tournament_id=tournament_id,
            name=name,
            is_duo=is_duo,
            groups_ideal=groups_ideal,
            performers_ideal=performers_ideal,
        )

    async def delete_with_cascade(self, id: uuid.UUID) -> bool:
        """Delete category using ORM to trigger cascade.

        Unlike base delete() which uses raw SQL, this method:
        1. Fetches the category object
        2. Uses session.delete() which triggers ORM cascade
        3. Properly deletes all child performers, pools, battles

        This fixes BR-FIX-002: Dancers can re-register in the same
        tournament after their category is deleted.

        Args:
            id: Category UUID

        Returns:
            True if deleted, False if not found
        """
        category = await self.get_by_id(id)
        if not category:
            return False
        await self.session.delete(category)
        await self.session.flush()
        return True
