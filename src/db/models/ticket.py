from sqlalchemy import(
    Column,
    DateTime,
    Integer,
    String,
    func,
    ForeignKey,
)
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
import uuid
import enum
from uuid import UUID
import sqlalchemy.dialects.postgresql as pg

# TYPE_CHECKING prevents circular imports
if TYPE_CHECKING:
    from .user import User


class TicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    PENDING = "pending"
    

class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class IssueType(enum.Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    ACCESS_PERMISSION = "access_permission"
    OTHER = "other"


class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    ticket_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            unique=True,
            nullable=False,
        )
    )
    subject: str = Field(nullable=False, max_length=200)
    description: str = Field(sa_column=Column(pg.TEXT, nullable=False))
    priority: TicketPriority = Field(
        sa_column=Column(
            pg.ENUM(TicketPriority, name="ticket_priority", create_type=True),
            nullable=False,
            default=TicketPriority.LOW,
        )
    )
    types_of_issue: IssueType = Field(
        sa_column=Column(
            pg.ENUM(IssueType, name="issue_types", create_type=True),
            nullable=False,
        )
    )
    status: TicketStatus = Field(
        sa_column=Column(
            pg.ENUM(TicketStatus, name="ticket_status", create_type=True),
            nullable=False,
            default=TicketStatus.OPEN,
        )
    )
    created_by: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    assigned_to: Optional[uuid.UUID] = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        )
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, onupdate=func.now())
    )

    # ✅ FIXED: Specify foreign_keys on BOTH sides using bracket notation
    created_by_user: "User" = Relationship(
        back_populates="tickets_created",
        sa_relationship_kwargs={
            "lazy": "joined",
            "foreign_keys": "[Ticket.created_by]"
        }
    )
    assigned_to_user: Optional["User"] = Relationship(
        back_populates="tickets_assigned",
        sa_relationship_kwargs={
            "lazy": "joined",
            "foreign_keys": "[Ticket.assigned_to]"
        }
    )