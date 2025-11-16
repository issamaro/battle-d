"""Tournament model."""
import enum
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.category import Category


class TournamentStatus(str, enum.Enum):
    """Tournament status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"


class TournamentPhase(str, enum.Enum):
    """Tournament phase enumeration.

    Phases always progress in this order (hardcoded, cannot skip):
    Registration → Preselection → Pools → Finals → Completed
    """

    REGISTRATION = "registration"
    PRESELECTION = "preselection"
    POOLS = "pools"
    FINALS = "finals"
    COMPLETED = "completed"

    @classmethod
    def get_next_phase(cls, current_phase: "TournamentPhase") -> "TournamentPhase":
        """Get the next phase in the sequence.

        Args:
            current_phase: Current tournament phase

        Returns:
            Next phase in the sequence

        Raises:
            ValueError: If current phase is already COMPLETED
        """
        phases = [
            cls.REGISTRATION,
            cls.PRESELECTION,
            cls.POOLS,
            cls.FINALS,
            cls.COMPLETED,
        ]
        try:
            current_index = phases.index(current_phase)
            if current_index >= len(phases) - 1:
                raise ValueError("Tournament already in COMPLETED phase")
            return phases[current_index + 1]
        except ValueError as e:
            if "not in list" in str(e):
                raise ValueError(f"Invalid phase: {current_phase}")
            raise


class Tournament(BaseModel):
    """Tournament model.

    Represents a competition event with multiple categories.

    Attributes:
        id: UUID primary key
        name: Tournament name
        status: Tournament status (active, completed)
        phase: Current global phase (applies to all categories)
        created_at: Creation timestamp
    """

    __tablename__ = "tournaments"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[TournamentStatus] = mapped_column(
        SQLEnum(TournamentStatus),
        default=TournamentStatus.ACTIVE,
        nullable=False,
    )

    phase: Mapped[TournamentPhase] = mapped_column(
        SQLEnum(TournamentPhase),
        default=TournamentPhase.REGISTRATION,
        nullable=False,
    )

    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Tournament(name={self.name}, phase={self.phase.value})>"

    def advance_phase(self) -> None:
        """Advance tournament to the next phase.

        Raises:
            ValueError: If already in COMPLETED phase
        """
        self.phase = TournamentPhase.get_next_phase(self.phase)
        if self.phase == TournamentPhase.COMPLETED:
            self.status = TournamentStatus.COMPLETED
