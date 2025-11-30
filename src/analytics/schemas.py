from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class TicketCountByStatus(BaseModel):
    open : int = 0
    approval_pending : int = 0
    pending : int = 0
    in_progress : int = 0
    resolved : int = 0
    closed : int = 0
    approved : int = 0

class TicketCountByPriority(BaseModel):
    low : int = 0
    medium : int = 0
    high : int = 0

class UserWithTicketStats(BaseModel):
    user_id: UUID
    username: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    resolved: int = 0
    pending: int = 0
    assigned_open: int = 0
    in_progress: int = 0
    approval_pending: int = 0
    approved: int = 0

class RoleTicketStatusBreakdown(BaseModel):
    role: str
    resolved: int = 0
    pending: int = 0
    assigned_open: int = 0
    in_progress: int = 0
    users: List[UserWithTicketStats] = []


class RoleTicketStatsResponse(BaseModel):
    results: List[RoleTicketStatusBreakdown]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[UUID] = None

class AnalyticsDashboardResponse(BaseModel):
    tickets_by_status: TicketCountByStatus
    tickets_by_priority: TicketCountByPriority
    tickets_opened_today: int
    overdue_tickets: int
    unassigned_tickets: int

class UsersWithStatsResponse(BaseModel):
    users: List[UserWithTicketStats]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
