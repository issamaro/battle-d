"""Battle model for competition bouts."""
import enum
import uuid
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Table,
    Column,
    Integer,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.performer import Performer


# Many-to-many association table for battle performers
battle_performers = Table(
    "battle_performers",
    Base.metadata,
    Column("battle_id", ForeignKey("battles.id", ondelete="CASCADE"), primary_key=True),
    Column("performer_id", ForeignKey("performers.id", ondelete="CASCADE"), primary_key=True),
)


class BattlePhase(str, enum.Enum):
    """Battle phase enumeration."""

    PRESELECTION = "preselection"
    POOLS = "pools"
    TIEBREAK = "tiebreak"
    FINALS = "finals"


class BattleStatus(str, enum.Enum):
    """Battle status enumeration."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class BattleOutcomeType(str, enum.Enum):
    """Battle outcome type enumeration.

    Different phases use different outcome formats:
    - Preselection: scored (0-10 per performer)
    - Pools: win_draw_loss
    - Tiebreak: tiebreak (judge votes)
    - Finals: win_loss
    """

    SCORED = "scored"  # Preselection: {performer_id: score}
    WIN_DRAW_LOSS = "win_draw_loss"  # Pools: {winner_id: uuid, is_draw: bool}
    TIEBREAK = "tiebreak"  # Tiebreak: {judge_votes: {...}, winner_ids: [...]}
    WIN_LOSS = "win_loss"  # Finals: {winner_id: uuid}


class Battle(BaseModel):
    """Battle model for competition bouts.

    Represents a single competition between performers.

    Attributes:
        id: UUID primary key
        category_id: Foreign key to category
        phase: Battle phase (preselection, pools, tiebreak, finals)
        status: Battle status (pending, active, completed)
        outcome_type: Type of outcome format
        winner_id: Foreign key to winning performer (nullable)
        outcome: JSON field with outcome data (format depends on outcome_type)
        created_at: Creation timestamp

    Constraints:
        Only one battle can have status='active' at any time (global)
    """

    __tablename__ = "battles"

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phase: Mapped[BattlePhase] = mapped_column(
        SQLEnum(BattlePhase),
        nullable=False,
        index=True,
    )

    status: Mapped[BattleStatus] = mapped_column(
        SQLEnum(BattleStatus),
        default=BattleStatus.PENDING,
        nullable=False,
        index=True,
    )

    outcome_type: Mapped[BattleOutcomeType] = mapped_column(
        SQLEnum(BattleOutcomeType),
        nullable=False,
    )

    winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("performers.id", ondelete="SET NULL"),
        nullable=True,
    )

    outcome: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    sequence_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Position in battle queue for ordering (BR-SCHED-001, BR-SCHED-002)",
    )

    # Table-level index for efficient ordering queries
    __table_args__ = (
        Index("idx_battles_category_sequence", "category_id", "sequence_order"),
    )

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="battles",
    )

    performers: Mapped[List["Performer"]] = relationship(
        "Performer",
        secondary=battle_performers,
        backref="battles",
    )

    winner: Mapped[Optional["Performer"]] = relationship(
        "Performer",
        foreign_keys=[winner_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Battle(phase={self.phase.value}, status={self.status.value})>"

    @property
    def performer_count(self) -> int:
        """Get number of performers in battle."""
        return len(self.performers)

    def set_scored_outcome(self, scores: Dict[str, float]) -> None:
        """Set scored outcome for preselection.

        Args:
            scores: Dictionary mapping performer_id (str) to score (float)
        """
        self.outcome_type = BattleOutcomeType.SCORED
        self.outcome = scores

    def set_win_draw_loss_outcome(
        self, winner_id: Optional[str], is_draw: bool = False
    ) -> None:
        """Set win/draw/loss outcome for pools.

        Args:
            winner_id: UUID of winner (None if draw)
            is_draw: Whether the battle was a draw
        """
        self.outcome_type = BattleOutcomeType.WIN_DRAW_LOSS
        self.outcome = {"winner_id": winner_id, "is_draw": is_draw}
        if winner_id:
            self.winner_id = uuid.UUID(winner_id)

    def set_tiebreak_outcome(
        self,
        judge_votes: Dict[str, str],
        winner_ids: List[str],
        n_participants: int,
        p_winners_needed: int,
    ) -> None:
        """Set tiebreak outcome.

        Args:
            judge_votes: Dictionary of judge votes {judge_id_round: performer_id}
            winner_ids: List of winner performer UUIDs
            n_participants: Number of tied participants
            p_winners_needed: Number of winners needed
        """
        self.outcome_type = BattleOutcomeType.TIEBREAK
        self.outcome = {
            "judge_votes": judge_votes,
            "winner_ids": winner_ids,
            "n_participants": n_participants,
            "p_winners_needed": p_winners_needed,
        }
        if len(winner_ids) == 1:
            self.winner_id = uuid.UUID(winner_ids[0])

    def set_win_loss_outcome(self, winner_id: str) -> None:
        """Set win/loss outcome for finals.

        Args:
            winner_id: UUID of winner
        """
        self.outcome_type = BattleOutcomeType.WIN_LOSS
        self.outcome = {"winner_id": winner_id}
        self.winner_id = uuid.UUID(winner_id)
