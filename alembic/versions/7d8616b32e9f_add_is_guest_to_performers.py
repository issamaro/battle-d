"""add_is_guest_to_performers

Revision ID: 7d8616b32e9f
Revises: 20251206_seq_order
Create Date: 2025-12-16 15:02:42.532575

Add is_guest boolean column to performers table for guest performer support.
Guests are pre-qualified performers who skip preselection with automatic 10.0 score.

Business Rules:
- BR-GUEST-001: Guest designation only allowed during Registration phase
- BR-GUEST-002: Guests automatically receive 10.0 preselection score
- BR-GUEST-003: Guests count toward pool capacity
- BR-GUEST-004: Each guest reduces minimum performer requirement by 1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d8616b32e9f'
down_revision: Union[str, None] = '20251206_seq_order'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_guest column with default False
    op.add_column(
        'performers',
        sa.Column('is_guest', sa.Boolean(), nullable=False, server_default='0')
    )

    # Add index on (category_id, is_guest) for efficient guest count queries
    op.create_index(
        'ix_performers_category_is_guest',
        'performers',
        ['category_id', 'is_guest'],
        unique=False
    )


def downgrade() -> None:
    # Remove index first
    op.drop_index('ix_performers_category_is_guest', table_name='performers')

    # Remove column
    op.drop_column('performers', 'is_guest')
