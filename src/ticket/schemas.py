from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid
from typing import Optional, List
from src.db.models.ticket import TicketStatus, TicketPriority, IssueType





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

    

class TicketDetails(TicketResponse):
    # Hint : Uncomment when we implement these relationships
    # replies: List["ReplyModel"] = []
    # attachments: List["AttachmentModel"] = []
    # ai_summaries: List["AISummaryModel"] = []
    pass


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

class TicketStatusModel(BaseModel):
    status : TicketStatus

class TicketPriorityUpdateRequest(BaseModel):
    priority : TicketPriority
