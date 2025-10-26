from pydantic import BaseModel
import uuid
from src.db.models.user import UserRole
from datetime import datetime


class UserResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserRoleUpdateRequest(BaseModel):
    role: UserRole


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
