"""Fix typo in Ticket.priority field

Revision ID: 9b9b3d809415
Revises: aa6f72d835b2
Create Date: 2025-10-16 03:34:07.505852
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b9b3d809415'
down_revision: Union[str, Sequence[str], None] = 'aa6f72d835b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely to rename 'prioroty' -> 'priority'."""
    # 1️⃣ Create ENUM type if not already existing
    ticket_priority_enum = postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', name='ticket_priority', create_type=False)

    # 2️⃣ Add the new column temporarily as nullable
    op.add_column(
        'tickets',
        sa.Column('priority', ticket_priority_enum, nullable=True)
    )

    # 3️⃣ Copy existing values from the old column
    op.execute("UPDATE tickets SET priority = prioroty")

    # 4️⃣ Alter column to NOT NULL
    op.alter_column('tickets', 'priority', nullable=False)

    # 5️⃣ Drop the old column
    op.drop_column('tickets', 'prioroty')


def downgrade() -> None:
    """Downgrade schema (reverse rename)."""
    ticket_priority_enum = postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', name='ticket_priority', create_type=False)

    op.add_column(
        'tickets',
        sa.Column('prioroty', ticket_priority_enum, nullable=True)
    )

    op.execute("UPDATE tickets SET prioroty = priority")

    op.alter_column('tickets', 'prioroty', nullable=False)
    op.drop_column('tickets', 'priority')
