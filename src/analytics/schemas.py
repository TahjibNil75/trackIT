from pydantic import BaseModel

class TicketCountByStatus(BaseModel):
    open : int = 0
    approval_pending : int = 0
    pending : int = 0
    in_progress : int = 0
    resolved : int = 0
    closed : int = 0
    approved : int = 0



class AnalyticsDashboardResponse(BaseModel):
    tickets_by_status: TicketCountByStatus
    tickets_opened_today: int
