from sqlalchemy import(
    Column,
    DateTime,
    Integer,
    String,
    func,
    ForeignKey,
)
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
import uuid
import enum
from uuid import UUID
import sqlalchemy.dialects.postgresql as pg

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    IT_SUPPORT = "it_support"
    MANAGER = "manager"

class TicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class IssueType(enum.Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    ACCESS_PERMISSION = "access_permission"
    OTHER = "other"

class User(SQLModel, table=True):
    __tablename__ = "users"
    user_id : uuid.UUID = Field(
        sa_column= Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            unique=True,
            nullable=False,
        )
    )
    username: str = Field(
        nullable=False,
    )
    email: str = Field(
        nullable=False,
        unique=True,
    )
    full_name: Optional[str] = None
    # exclude=True → prevent password_hash from being included
    # in API responses or model dumps for security reasons.
    password_hash: str = Field(exclude=True)
    role : UserRole = Field(
        sa_column=Column(
            pg.ENUM(
                UserRole,
                name="user_roles",
                create_type=True,  # Automatically create the ENUM type in the DB
            ),
            nullable=False,
            default=UserRole.USER,
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
            onupdate=func.now(),
        )
    )



class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    ticket_id : uuid.UUID = Field(
        sa_column = Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            unique=True,
            nullable=False,
        )
    )
    subject: str = Field(
        nullable=False,
        max_length=200,
    )
    description : str = Field(
        sa_column=Column(
            pg.TEXT,
            nullable=False,
        )
    )
    # prioroty : TicketPriority = Field(
    priority : TicketPriority = Field(  # ✅ fixed spelling here
        sa_column=Column(
            pg.ENUM(
                TicketPriority,
                name="ticket_priority",
                create_type=True,
            ),
            nullable=False,
            default=TicketPriority.LOW,
        )
    )
    types_of_issue : IssueType = Field(
        sa_column = Column(
            pg.ENUM(
                IssueType,
                name = "issue_types",
                create_type=True,
            ),
            nullable=False,
        )
    )
    status : TicketStatus = Field(
        sa_column = Column(
            pg.ENUM(
                TicketStatus,
                name="ticket_status",
                create_type=True,
            ),
            nullable=False,
            default=TicketStatus.OPEN,
        )
    )
    created_by : uuid.UUID = Field(
        sa_column = Column(
            pg.UUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    assigned_to : Optional[uuid.UUID] = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        )
    )
    created_at : datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
        )
    )
    updated_at : datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            onupdate=func.now(),
        )
    )