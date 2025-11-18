from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import TicketCountByStatus, AnalyticsDashboardResponse
from sqlmodel import select, func
from src.db.models.ticket import Ticket
from datetime import datetime, timedelta
from sqlalchemy import cast, Date


class AnalyticsService:

    # ==================== Helper Methods ====================


    async def get_tickets_by_status(
            self,
            session : AsyncSession
    ) -> TicketCountByStatus:
        tickets = await session.execute(
            select(
                Ticket.status,
                func.count(Ticket.ticket_id).label("count")
            )
            .group_by(Ticket.status)
        )
        status_counts = {
            row.status.value: row.count for row in tickets.all()
        }

        return TicketCountByStatus(
            open=status_counts.get("open", 0),
            in_progress=status_counts.get("in_progress", 0),
            resolved=status_counts.get("resolved", 0),
            closed=status_counts.get("closed", 0),
            approval_pending=status_counts.get("approval_pending", 0),
            approved=status_counts.get("approved", 0),
            pending=status_counts.get("pending", 0)
        )
    

    async def get_tickets_opened_today(
            self,
            session : AsyncSession
    ) -> int:
        
        today_utc = datetime.utcnow().date()
        tickets = await session.execute(
            select(func.count(Ticket.ticket_id))
            .where(
                cast(Ticket.created_at, Date) == today_utc
            )
        )
        return tickets.scalar_one() or 0
        






    # ==================== Main Service Method ====================

    async def get_analytics_dashboard(
            self,
            session : AsyncSession,
            page: int = 1,
            page_size: int = 10
    ) -> AnalyticsDashboardResponse:
        tickets_by_status = await self.get_tickets_by_status(session)
        tickets_opened_today = await self.get_tickets_opened_today(session)

        return AnalyticsDashboardResponse(
            tickets_by_status=tickets_by_status,
            tickets_opened_today=tickets_opened_today
        )