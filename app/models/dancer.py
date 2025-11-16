"""Dancer model for performers (no login credentials)."""
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.performer import Performer


class Dancer(BaseModel):
    """Dancer model for performers.

    Dancers are performers who participate in tournaments.
    They do NOT have login credentials - they're managed by staff.

    Attributes:
        id: UUID primary key
        email: Unique contact email
        first_name: Dancer's first name
        last_name: Dancer's last name
        date_of_birth: Birth date
        blaze: Stage name (primary identifier in battles)
        country: Country (optional)
        city: City (optional)
        created_at: Record creation timestamp
    """

    __tablename__ = "dancers"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    blaze: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,  # Frequently searched
    )

    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    performers: Mapped[List["Performer"]] = relationship(
        "Performer",
        back_populates="dancer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Dancer(blaze={self.blaze}, email={self.email})>"

    @property
    def full_name(self) -> str:
        """Get dancer's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        """Calculate dancer's current age."""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
