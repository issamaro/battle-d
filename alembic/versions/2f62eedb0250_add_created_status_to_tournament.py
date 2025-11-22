"""add_created_status_to_tournament

Revision ID: 2f62eedb0250
Revises: 564aa650e093
Create Date: 2025-11-19 21:48:25.502701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f62eedb0250'
down_revision: Union[str, None] = '564aa650e093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'created' value to TournamentStatus enum
    # SQLite doesn't support ALTER TYPE for enums, so we need to:
    # 1. Create new column with new enum
    # 2. Copy data
    # 3. Drop old column
    # 4. Rename new column

    # For SQLite, we use a simpler approach with CHECK constraints
    # The enum is validated at the application level

    # Add the new enum value by recreating the check constraint
    # SQLite doesn't have ALTER TYPE, so the enum is enforced by application
    # No database migration needed for SQLite enum values

    # However, we need to update the default value
    op.execute("UPDATE tournaments SET status = 'created' WHERE status = 'active' AND phase = 'registration'")

    # Note: For PostgreSQL, you would use:
    # op.execute("ALTER TYPE tournamentstatus ADD VALUE 'created' BEFORE 'active'")


def downgrade() -> None:
    # Revert CREATED tournaments back to ACTIVE
    op.execute("UPDATE tournaments SET status = 'active' WHERE status = 'created'")
