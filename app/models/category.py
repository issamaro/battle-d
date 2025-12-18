"""Category model (1v1 or 2v2 competition categories)."""
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.utils.tournament_calculations import calculate_minimum_performers

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.performer import Performer
    from app.models.pool import Pool
    from app.models.battle import Battle


class Category(BaseModel):
    """Category model for competition categories.

    Examples: "Hip Hop Boys 1v1", "Krump Duo 2v2"

    Attributes:
        id: UUID primary key
        tournament_id: Foreign key to tournament
        name: Category name
        is_duo: False for 1v1, True for 2v2
        groups_ideal: Target number of pools (default 2)
        performers_ideal: Target performers per pool (default 4)
        created_at: Creation timestamp
    """

    __tablename__ = "categories"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_duo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    groups_ideal: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=False,
    )

    performers_ideal: Mapped[int] = mapped_column(
        Integer,
        default=4,
        nullable=False,
    )

    # Relationships
    tournament: Mapped["Tournament"] = relationship(
        "Tournament",
        back_populates="categories",
    )

    performers: Mapped[List["Performer"]] = relationship(
        "Performer",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    pools: Mapped[List["Pool"]] = relationship(
        "Pool",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    battles: Mapped[List["Battle"]] = relationship(
        "Battle",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Category(name={self.name}, is_duo={self.is_duo})>"

    @property
    def category_type(self) -> str:
        """Get category type as string."""
        return "2v2" if self.is_duo else "1v1"

    @property
    def ideal_pool_capacity(self) -> int:
        """Calculate ideal total pool capacity.

        Returns:
            Total number of performers that should qualify for pools
        """
        return self.groups_ideal * self.performers_ideal

    @property
    def minimum_performers_required(self) -> int:
        """Calculate minimum performers required to start category.

        Formula: (groups_ideal × 2) + 1 per BR-MIN-001

        This ensures:
        - At least 2 performers per pool (groups_ideal × 2)
        - At least 1 performer eliminated in preselection (+1)

        Returns:
            Minimum number of registered performers required
        """
        return calculate_minimum_performers(self.groups_ideal)
