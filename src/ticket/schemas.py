from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid 
from typing import Optional, List
from src.db.models.ticket import TicketStatus, TicketPriority, IssueType
from src.comment.schemas import CommentResponse








class AttachmentResponse(BaseModel):
    attachment_id : uuid.UUID
    ticket_id : uuid.UUID
    file_name : str
    file_url : str
    file_type : str
    uploaded_at : datetime

    class Config:
        orm_mode = True

class TicketResponse(BaseModel):
    ticket_id : uuid.UUID
    subject : str
    description : str
    priority : TicketPriority
    types_of_issue : IssueType
    status : TicketStatus
    created_by : uuid.UUID
    assigned_to : Optional[uuid.UUID]
    created_at : datetime
    updated_at : datetime
    attachments: Optional[List[AttachmentResponse]] = []

    class Config:
        orm_mode = True

    

class TicketDetails(TicketResponse):
    # Hint : Uncomment when we implement these relationships
    # replies: List["ReplyModel"] = []
    # ai_summaries: List["AISummaryModel"] = []
    comments : List[CommentResponse] = []
    
class TicketSummaryResponse(BaseModel):
    ticket_id: uuid.UUID
    subject: str
    priority: TicketPriority
    types_of_issue: IssueType
    status: TicketStatus
    created_by: uuid.UUID
    assigned_to: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TicketCreateRequest(BaseModel):
    subject : str = Field(
        ..., 
        min_length=5,
        max_length=200, 
    )
    description : str = Field(
        ..., 
        min_length=10,
    )
    priority : TicketPriority = TicketPriority.MEDIUM
    types_of_issue : IssueType
    assigned_to : Optional[uuid.UUID] = None


class TicketUpdateRequest(BaseModel):
    subject : Optional[str] = Field(
        None,
        min_length=5,
        max_length=200,
    )
    description : Optional[str] = Field(
        None,
        min_length=10,
    )
    priority : Optional[TicketPriority] = None
    types_of_issue : Optional[IssueType] = None
    assigned_to : Optional[uuid.UUID] = None
    status: Optional[TicketStatus] = None  


class TicketHistoryListResponse(BaseModel):
    history_id: uuid.UUID
    ticket_id: uuid.UUID
    action_type: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: uuid.UUID
    changed_at: datetime

    class Config:
        from_attributes = True


class TicketHistoryPaginatedResponse(BaseModel):
    histories: List[TicketHistoryListResponse]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True