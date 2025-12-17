"""Performer model (dancer in tournament context)."""
import uuid
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    String,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.dancer import Dancer
    from app.models.tournament import Tournament
    from app.models.category import Category


class Performer(BaseModel):
    """Performer model linking a dancer to a tournament category.

    Represents tournament-specific participation with stats.

    Attributes:
        id: UUID primary key
        tournament_id: Foreign key to tournament
        category_id: Foreign key to category
        dancer_id: Foreign key to dancer
        duo_partner_id: Foreign key to partner performer (nullable, for 2v2)
        is_guest: Whether performer is a guest (skips preselection with 10.0 score)
        preselection_score: Average score from preselection (nullable, or 10.0 for guests)
        pool_wins: Number of pool wins (default 0)
        pool_draws: Number of pool draws (default 0)
        pool_losses: Number of pool losses (default 0)
        created_at: Creation timestamp

    Constraints:
        One dancer can only register in one category per tournament

    Business Rules:
        BR-GUEST-001: Guest designation only allowed during Registration phase
        BR-GUEST-002: Guests automatically receive 10.0 preselection score
        BR-GUEST-003: Guests count toward pool capacity
        BR-GUEST-004: Each guest reduces minimum performer requirement by 1
    """

    __tablename__ = "performers"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dancer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dancers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    duo_partner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("performers.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_guest: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    preselection_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )

    pool_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    pool_draws: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    pool_losses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    dancer: Mapped["Dancer"] = relationship(
        "Dancer",
        back_populates="performers",
    )

    tournament: Mapped["Tournament"] = relationship(
        "Tournament",
    )

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="performers",
    )

    duo_partner: Mapped[Optional["Performer"]] = relationship(
        "Performer",
        remote_side="Performer.id",
        foreign_keys=[duo_partner_id],
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "dancer_id",
            "tournament_id",
            name="uq_dancer_tournament",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Performer(dancer_id={self.dancer_id}, category_id={self.category_id})>"

    @property
    def pool_points(self) -> int:
        """Calculate pool points.

        Points = (wins × 3) + (draws × 1) + (losses × 0)

        Returns:
            Total pool points
        """
        return (self.pool_wins * 3) + (self.pool_draws * 1)

    def add_pool_win(self) -> None:
        """Record a pool win."""
        self.pool_wins += 1

    def add_pool_draw(self) -> None:
        """Record a pool draw."""
        self.pool_draws += 1

    def add_pool_loss(self) -> None:
        """Record a pool loss."""
        self.pool_losses += 1
