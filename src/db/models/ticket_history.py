from sqlmodel import SQLModel, Field, Relationship, String
import uuid
from sqlalchemy import Column, DateTime, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .ticket import Ticket

class TicketHistory(SQLModel, table=True):
    __tablename__ = "ticket_history"

    history_id : uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            unique=True,
            nullable=False
        )
    )

    ticket_id : uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            ForeignKey("tickets.ticket_id", ondelete="CASCADE"),
            nullable=False
        )
    )

    action_type : str = Field(  # examples: created, status_changed, priority_changed, assigned, reassigned, updated
        sa_column=Column(
            String(50),
            nullable=False
        )
    )

    old_value : Optional[str] = Field(default=None)
    new_value : Optional[str] = Field(default=None)

    changed_by : uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=False
        )
    )

    changed_at : datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False)
    )

    ticket: "Ticket" = Relationship(back_populates="history")

