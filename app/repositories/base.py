"""Base repository with common CRUD operations."""
import uuid
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations.

    All repositories should inherit from this class.

    Type Parameters:
        ModelType: The model class this repository manages
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """Initialize repository.

        Args:
            model: The model class
            session: Database session
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        """Get a record by ID.

        Args:
            id: Record UUID

        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[ModelType]:
        """Get all records with optional pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        query = select(self.model)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(
        self, id: uuid.UUID, **kwargs: Any
    ) -> Optional[ModelType]:
        """Update a record by ID.

        Args:
            id: Record UUID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by ID.

        Args:
            id: Record UUID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

    async def exists(self, id: uuid.UUID) -> bool:
        """Check if a record exists.

        Args:
            id: Record UUID

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        """Count total records.

        Returns:
            Total number of records
        """
        result = await self.session.execute(
            select(self.model.id)
        )
        return len(list(result.scalars().all()))
