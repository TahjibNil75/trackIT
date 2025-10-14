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
