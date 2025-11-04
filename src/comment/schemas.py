from pydantic import BaseModel, Field
import uuid
from src.db.models.comment import CommentVisibility
from datetime import datetime


class CommentCreateRequest(BaseModel):
    content : str = Field(
        ...,
        min_length=1,
        max_length=1000
    )
    ticket_id: uuid.UUID
    visibility: CommentVisibility = CommentVisibility.PUBLIC


class CommentResponse(BaseModel):
    comment_id : uuid.UUID
    content : str
    ticket_id : uuid.UUID
    user_id : uuid.UUID
    visibility : CommentVisibility
    created_at : datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CommentUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
