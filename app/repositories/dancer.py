"""Dancer repository for performer management."""
from datetime import date
from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dancer import Dancer
from app.repositories.base import BaseRepository


class DancerRepository(BaseRepository[Dancer]):
    """Repository for Dancer model.

    Handles performer (dancer) queries and operations.
    """

    def __init__(self, session: AsyncSession):
        """Initialize DancerRepository.

        Args:
            session: Database session
        """
        super().__init__(Dancer, session)

    async def get_by_email(self, email: str) -> Optional[Dancer]:
        """Get dancer by email address.

        Args:
            email: Dancer email

        Returns:
            Dancer instance or None if not found
        """
        result = await self.session.execute(
            select(Dancer).where(Dancer.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_blaze(self, blaze: str) -> Optional[Dancer]:
        """Get dancer by stage name (blaze).

        Args:
            blaze: Stage name

        Returns:
            Dancer instance or None if not found
        """
        result = await self.session.execute(
            select(Dancer).where(Dancer.blaze == blaze)
        )
        return result.scalar_one_or_none()

    async def search(self, query: str, limit: int = 20) -> List[Dancer]:
        """Search dancers by blaze, name, or email.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching dancers
        """
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Dancer)
            .where(
                or_(
                    Dancer.blaze.ilike(search_pattern),
                    Dancer.first_name.ilike(search_pattern),
                    Dancer.last_name.ilike(search_pattern),
                    Dancer.email.ilike(search_pattern),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered.

        Args:
            email: Email to check

        Returns:
            True if email exists, False otherwise
        """
        result = await self.session.execute(
            select(Dancer.id).where(Dancer.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def create_dancer(
        self,
        email: str,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        blaze: str,
        country: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Dancer:
        """Create a new dancer.

        Args:
            email: Dancer email (must be unique)
            first_name: First name
            last_name: Last name
            date_of_birth: Birth date
            blaze: Stage name
            country: Country (optional)
            city: City (optional)

        Returns:
            Created dancer instance
        """
        return await self.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            blaze=blaze,
            country=country,
            city=city,
        )
