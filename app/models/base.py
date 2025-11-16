"""Base model with common fields for all models."""
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class BaseModel(Base):
    """Base model with UUID primary key and timestamps.

    All models should inherit from this class.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            dict: Model as dictionary
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Convert UUID to string, datetime to ISO format
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
