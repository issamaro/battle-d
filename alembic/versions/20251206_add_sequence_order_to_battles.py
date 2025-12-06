"""Add sequence_order to battles for BR-SCHED-001 and BR-SCHED-002

Revision ID: 20251206_seq_order
Revises: 8d4205ef8195
Create Date: 2025-12-06

Business Rules:
- BR-SCHED-001: Battle queue interleaving across categories
- BR-SCHED-002: Battle reordering constraints (locked positions)

Changes:
- Add sequence_order column to battles table (nullable integer)
- Add index on (category_id, sequence_order) for efficient ordering queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251206_seq_order'
down_revision: Union[str, None] = '8d4205ef8195'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sequence_order column to battles table
    op.add_column(
        'battles',
        sa.Column('sequence_order', sa.Integer(), nullable=True)
    )

    # Add composite index for efficient ordering queries
    op.create_index(
        'idx_battles_category_sequence',
        'battles',
        ['category_id', 'sequence_order'],
        unique=False
    )

    # Data migration: Set initial sequence_order based on created_at
    # This preserves existing battle order
    op.execute("""
        UPDATE battles
        SET sequence_order = (
            SELECT COUNT(*)
            FROM battles b2
            WHERE b2.category_id = battles.category_id
            AND b2.created_at <= battles.created_at
        )
        WHERE sequence_order IS NULL
    """)


def downgrade() -> None:
    # Remove index first
    op.drop_index('idx_battles_category_sequence', table_name='battles')

    # Remove column
    op.drop_column('battles', 'sequence_order')
