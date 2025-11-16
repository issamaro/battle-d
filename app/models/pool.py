"""Pool model for pool phase groups."""
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.performer import Performer
    from app.models.battle import Battle


# Many-to-many association table for pool performers
pool_performers = Table(
    "pool_performers",
    Base.metadata,
    Column("pool_id", ForeignKey("pools.id", ondelete="CASCADE"), primary_key=True),
    Column("performer_id", ForeignKey("performers.id", ondelete="CASCADE"), primary_key=True),
)


class Pool(BaseModel):
    """Pool model for pool phase groups.

    Represents a group in the pool phase where performers compete round-robin.

    Attributes:
        id: UUID primary key
        category_id: Foreign key to category
        name: Pool name (e.g., "Pool A", "Pool B")
        winner_id: Foreign key to winning performer (nullable)
        created_at: Creation timestamp
    """

    __tablename__ = "pools"

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("performers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="pools",
    )

    performers: Mapped[List["Performer"]] = relationship(
        "Performer",
        secondary=pool_performers,
        backref="pools",
    )

    winner: Mapped[Optional["Performer"]] = relationship(
        "Performer",
        foreign_keys=[winner_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Pool(name={self.name}, category_id={self.category_id})>"

    @property
    def performer_count(self) -> int:
        """Get number of performers in pool."""
        return len(self.performers)
