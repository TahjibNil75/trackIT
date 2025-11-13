from sqlmodel import SQLModel, Field, Relationship
import uuid
from sqlalchemy import Column, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .ticket import Ticket


class Attachment(SQLModel, table=True):
    __tablename__ = "attachments"


    attachment_id : uuid.UUID = Field(
        sa_column = Column(
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
            nullable=False,
        )
    )

    file_name : str = Field(nullable=False)
    file_url : str = Field(nullable=False)
    file_type : str = Field(nullable=False)
    uploaded_at : datetime = Field(
        default_factory=datetime.utcnow
    )
    ticket : Optional["Ticket"] = Relationship(
        back_populates="attachments"
    )


