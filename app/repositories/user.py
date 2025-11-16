"""User repository for system account management."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model.

    Handles system account queries and operations.
    """

    def __init__(self, session: AsyncSession):
        """Initialize UserRepository.

        Args:
            session: Database session
        """
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.

        Args:
            email: User email

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role.

        Args:
            role: User role to filter by

        Returns:
            List of users with the given role
        """
        result = await self.session.execute(
            select(User).where(User.role == role)
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
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def create_user(
        self, email: str, first_name: str, role: UserRole
    ) -> User:
        """Create a new user account.

        Args:
            email: User email (must be unique)
            first_name: User's first name
            role: User role

        Returns:
            Created user instance
        """
        return await self.create(
            email=email,
            first_name=first_name,
            role=role,
        )
