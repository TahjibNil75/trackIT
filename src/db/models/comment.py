from sqlalchemy import Column, ForeignKey, Text
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import uuid
import sqlalchemy.dialects.postgresql as pg

# TYPE_CHECKING prevents circular imports
if TYPE_CHECKING:
    from .user import User
    from .ticket import Ticket

class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    comment_id : uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            unique=True,
            nullable=False
        )
    )

    content : str = Field(
        sa_column=  Column(
            Text,
            nullable=False
        )
    )

    ticket_id : uuid.UUID = Field(
        sa_column= Column(
            pg.UUID(as_uuid=True),
            ForeignKey("tickets.ticket_id", ondelete="CASCADE"),
            nullable=False
        )
    )

    user_id : uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False
        )
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
        )
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            onupdate=datetime.utcnow,
        )
    )

    # Relationships
    ticket : "Ticket" = Relationship(
        back_populates="comments",
        sa_relationship_kwargs={"lazy" : "joined"}
    )

    user : "User" = Relationship(
        back_populates="comments",
        sa_relationship_kwargs={"lazy" : "joined"}
    )

