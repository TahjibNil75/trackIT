from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import TicketCountByStatus, AnalyticsDashboardResponse, RoleTicketStatsResponse, RoleTicketStatusBreakdown
from sqlmodel import select, func
from src.db.models.ticket import Ticket, TicketStatus
from src.db.models.user import User, UserRole
from datetime import datetime, timedelta
from sqlalchemy import cast, Date
from typing import Optional, Dict
from uuid import UUID


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
            tickets_opened_today=tickets_opened_today,
        )
    

    async def SupportMetricsService(
            self,
            session : AsyncSession,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            user_id: Optional[UUID] = None,
            roles: Optional[list[str]] = None

    ) -> RoleTicketStatsResponse:
        
        # Validate roles against allowed enum values
        valid_role_values = {role.value for role in UserRole}
        if roles:
            filtered_roles = [role for role in roles if role in valid_role_values]
        else:
            filtered_roles = []

        # If user_id is provided → only get that user's role
        if user_id:
            user_role_row = await session.execute(
                select(User.role).where(User.user_id == user_id)
            )
            user_role = user_role_row.scalar()
            if user_role:
                filtered_roles = [user_role.value]

        if not filtered_roles:
            filtered_roles = ["admin", "it_support", "manager"]

        statement = (
            select(
                User.role,
                Ticket.status,
                func.count(Ticket.ticket_id).label("count")
            )
            .join(User, Ticket.assigned_to == User.user_id)
        )

        # Apply filters
        if start_date:
            statement = statement.where(Ticket.created_at >= start_date)
        if end_date:
            statement = statement.where(Ticket.created_at <= end_date)
        if user_id:
            statement = statement.where(Ticket.assigned_to == user_id)
    
        # Filter by roles
        try:
            role_enums = [UserRole(role) for role in filtered_roles]
            statement = statement.where(User.role.in_(role_enums))
        except ValueError as e:
            raise ValueError(f"Invalid role provided: {e}")
        
        # Group by role and status
        statement = statement.group_by(User.role, Ticket.status)
        role_status_counts = await session.execute(statement)

        # Initialize role breakdowns with zero counts for all filtered roles
        # role_breakdowns = {
        #     role: {
        #         "role": role,
        #         "resolved": 0,
        #         "pending": 0,
        #         "assigned_open": 0,
        #         "in_progress": 0
        #     }
        #     for role in filtered_roles
        # }

        role_breakdowns: Dict[str, RoleTicketStatusBreakdown] = {
            role: RoleTicketStatusBreakdown(role=role) for role in filtered_roles
        }

        for row in role_status_counts.all():
            if row.role is None or row.status is None:
                continue

            role_value = row.role.value
            status_value = row.status.value

            # Skip roles that weren't in our filtered list
            if role_value not in role_breakdowns:
                continue

            # Map status to the appropriate field in the breakdown
            if status_value == TicketStatus.RESOLVED.value:
                role_breakdowns[role_value].resolved = row.count
            elif status_value == TicketStatus.PENDING.value:
                role_breakdowns[role_value].pending = row.count
            elif status_value == TicketStatus.OPEN.value:
                role_breakdowns[role_value].assigned_open = row.count
            elif status_value == TicketStatus.IN_PROGRESS.value:
                role_breakdowns[role_value].in_progress = row.count

            
        return RoleTicketStatsResponse(
            results=list(role_breakdowns.values()),
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
