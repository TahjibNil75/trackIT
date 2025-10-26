"""feat: safely add is_active field in user model

Revision ID: 46da3ee68328
Revises: 342909719407
Create Date: 2025-10-23 16:34:58.185958
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46da3ee68328'
down_revision: Union[str, Sequence[str], None] = '342909719407'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely."""
    # ✅ Step 1: add column with a temporary server default
    op.add_column(
        'users',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )

    # ✅ Step 2: backfill data for all existing users
    op.execute("UPDATE users SET is_active = true")

    # ✅ Step 3: remove the server default (optional cleanup)
    op.alter_column('users', 'is_active', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_active')
