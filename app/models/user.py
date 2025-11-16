"""User model for system accounts (admin, staff, mc, judge)."""
import enum
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """User role enumeration.

    Roles:
        admin: Full access, can advance phases, create users
        staff: Can manage dancers, tournaments, encode results
        mc: Read-only access for ceremony hosting
        judge: Scoring access (V2 only)
    """

    ADMIN = "admin"
    STAFF = "staff"
    MC = "mc"
    JUDGE = "judge"


class User(BaseModel):
    """User model for system accounts.

    Users are people who access the application, not dancers.
    Dancers don't have login credentials.

    Attributes:
        id: UUID primary key
        email: Unique email address
        first_name: User's first name
        role: User role (admin, staff, mc, judge)
        created_at: Account creation timestamp
    """

    __tablename__ = "users"

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

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(email={self.email}, role={self.role.value})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_staff(self) -> bool:
        """Check if user is staff or admin."""
        return self.role in (UserRole.ADMIN, UserRole.STAFF)

    @property
    def is_mc(self) -> bool:
        """Check if user is MC, staff, or admin."""
        return self.role in (UserRole.ADMIN, UserRole.STAFF, UserRole.MC)

    @property
    def is_judge(self) -> bool:
        """Check if user is judge."""
        return self.role == UserRole.JUDGE
