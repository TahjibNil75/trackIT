from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import TicketCountByStatus, TicketCountByPriority, AnalyticsDashboardResponse, RoleTicketStatsResponse, RoleTicketStatusBreakdown, UserWithTicketStats, UsersWithStatsResponse
from sqlmodel import select, func
from src.db.models.ticket import Ticket, TicketStatus
from src.db.models.user import User, UserRole
from src.user.service import UserManagementService
from datetime import datetime, timedelta
from sqlalchemy import cast, Date
from typing import Optional, Dict
from uuid import UUID


class AnalyticsService:
    def __init__(self):
        self.user_service = UserManagementService() ## Import User Management Service

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
    

    # ==================== Support Metrics Helper Methods ====================

    async def _validate_and_filter_roles(
            self,
            session: AsyncSession,
            roles: Optional[list[str]] = None,
            user_id: Optional[UUID] = None
    ) -> list[str]:
        """Validate and filter roles based on input parameters."""
        valid_role_values = {role.value for role in UserRole}
        
        # Filter valid roles from input
        if roles:
            filtered_roles = [role for role in roles if role in valid_role_values]
        else:
            filtered_roles = []

        # If user_id is provided, get that user's role
        if user_id:
            user_role_row = await session.execute(
                select(User.role).where(User.user_id == user_id)
            )
            user_role = user_role_row.scalar()
            if user_role:
                filtered_roles = [user_role.value]

        # Default to admin, it_support, and manager if no roles specified
        if not filtered_roles:
            filtered_roles = ["admin", "it_support", "manager"]

        return filtered_roles

    def _build_role_ticket_stats_query(
            self,
            filtered_roles: list[str],
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            user_id: Optional[UUID] = None
    ):
        """Build the query for role-level ticket statistics."""
        statement = (
            select(
                User.role,
                Ticket.status,
                func.count(Ticket.ticket_id).label("count")
            )
            .join(User, Ticket.assigned_to == User.user_id)
        )

        # Apply date filters
        if start_date:
            statement = statement.where(Ticket.created_at >= start_date)
        if end_date:
            statement = statement.where(Ticket.created_at <= end_date)
        
        # Apply user filter
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
        
        return statement

    def _aggregate_role_ticket_counts(
            self,
            role_status_counts,
            filtered_roles: list[str]
    ) -> Dict[str, RoleTicketStatusBreakdown]:
        """Aggregate ticket counts by role and status."""
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

        return role_breakdowns

    async def _get_users_by_role(
            self,
            session: AsyncSession,
            role_enum: UserRole
    ) -> list[User]:
        """Get all users for a specific role."""
        if role_enum == UserRole.ADMIN:
            return await self.user_service.get_all_admins(session)
        elif role_enum == UserRole.IT_SUPPORT:
            return await self.user_service.get_all_support(session)
        elif role_enum == UserRole.MANAGER:
            return await self.user_service.get_all_managers(session)
        else:
            return []

    async def _calculate_user_ticket_stats(
            self,
            session: AsyncSession,
            user: User,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Calculate ticket statistics for a single user."""
        ticket_stats_query = (
            select(
                Ticket.status,
                func.count(Ticket.ticket_id).label("count")
            )
            .where(Ticket.assigned_to == user.user_id)
        )
        
        # Apply date filters if provided
        if start_date:
            ticket_stats_query = ticket_stats_query.where(Ticket.created_at >= start_date)
        if end_date:
            ticket_stats_query = ticket_stats_query.where(Ticket.created_at <= end_date)
        
        ticket_stats_query = ticket_stats_query.group_by(Ticket.status)
        ticket_stats_result = await session.execute(ticket_stats_query)
        
        # Initialize counts
        stats = {
            "resolved": 0,
            "pending": 0,
            "assigned_open": 0,
            "in_progress": 0,
            "approval_pending" : 0,
            "approved" : 0,
        }
        
        # Aggregate ticket counts by status
        for stat_row in ticket_stats_result.all():
            if stat_row.status == TicketStatus.RESOLVED:
                stats["resolved"] = stat_row.count
            elif stat_row.status == TicketStatus.PENDING:
                stats["pending"] = stat_row.count
            elif stat_row.status == TicketStatus.OPEN:
                stats["assigned_open"] = stat_row.count
            elif stat_row.status == TicketStatus.IN_PROGRESS:
                stats["in_progress"] = stat_row.count
            elif stat_row.status == TicketStatus.APPROVAL_PENDING:
                stats["approval_pending"] = stat_row.count
            elif stat_row.status == TicketStatus.APPROVED:
                stats["approved"] = stat_row.count
        
        return stats

    async def _get_users_with_ticket_stats(
            self,
            session: AsyncSession,
            role_value: str,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> list[UserWithTicketStats]:
        """Get all users for a role with their ticket statistics."""
        users_list = []
        
        try:
            role_enum = UserRole(role_value)
            users = await self._get_users_by_role(session, role_enum)
            
            # Calculate ticket stats for each user
            for user in users:
                stats = await self._calculate_user_ticket_stats(
                    session, user, start_date, end_date
                )
                
                # Create user with ticket stats
                user_with_stats = UserWithTicketStats(
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role.value,
                    is_active=user.is_active,
                    resolved=stats["resolved"],
                    pending=stats["pending"],
                    assigned_open=stats["assigned_open"],
                    in_progress=stats["in_progress"]
                )
                users_list.append(user_with_stats)
                
        except ValueError:
            # Invalid role, skip
            pass
        
        return users_list

    # ==================== Main Service Method ====================

    async def SupportMetricsService(
            self,
            session: AsyncSession,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            user_id: Optional[UUID] = None,
            roles: Optional[list[str]] = None
    ) -> RoleTicketStatsResponse:
        """Get support metrics grouped by role with user details and ticket statistics."""
        
        # Step 1: Validate and filter roles
        filtered_roles = await self._validate_and_filter_roles(
            session, roles, user_id
        )

        # Step 2: Build and execute query for role-level ticket stats
        statement = self._build_role_ticket_stats_query(
            filtered_roles, start_date, end_date, user_id
        )
        role_status_counts = await session.execute(statement)

        # Step 3: Aggregate ticket counts by role
        role_breakdowns = self._aggregate_role_ticket_counts(
            role_status_counts, filtered_roles
        )

        # Step 4: Fetch users with ticket stats for each role
        for role_value in filtered_roles:
            users_with_stats = await self._get_users_with_ticket_stats(
                session, role_value, start_date, end_date
            )
            role_breakdowns[role_value].users = users_with_stats
            
        return RoleTicketStatsResponse(
            results=list(role_breakdowns.values()),
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
    
    # ==================== Users Stats Helper Methods ====================

    async def _get_all_users_with_stats(
            self,
            session: AsyncSession,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
    ) -> list[UserWithTicketStats]:
        """Get all users with their ticket statistics."""
        all_users_result = await session.execute(select(User))
        all_users = all_users_result.scalars().all()

        all_users_with_stats = []
        for user in all_users:
            stats = await self._calculate_user_ticket_stats(
                session, user, start_date, end_date
            )
            user_with_stats = UserWithTicketStats(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                resolved=stats["resolved"],
                pending=stats["pending"],
                assigned_open=stats["assigned_open"],
                in_progress=stats["in_progress"],
                approval_pending = stats["approval_pending"],
                approved = stats["approved"],
            )
            all_users_with_stats.append(user_with_stats)

        return all_users_with_stats
    
    async def _get_users_by_role_with_stats(
            self,
            session: AsyncSession,
            roles: list[str],
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> list[UserWithTicketStats]:
        """Get users filtered by roles with their ticket statistics."""
        filtered_roles = await self._validate_and_filter_roles(
            session, roles, None
        )
        all_users_with_stats = []
        for role_value in filtered_roles:
            users_with_stats = await self._get_users_with_ticket_stats(
                session, role_value, start_date, end_date
            )
            all_users_with_stats.extend(users_with_stats)

        return all_users_with_stats
    
    def _filter_users_by_profile_field(
            self,
            users: list[UserWithTicketStats],
            full_name: Optional[str] = None,
            email: Optional[str] = None,
            username: Optional[str] = None
    ) -> list[UserWithTicketStats]:
        """Filter users based on profile fields."""
        filtered_users = users

        if full_name:
            filtered_users = [
                user for user in filtered_users
                if user.full_name and full_name.lower() in user.full_name.lower()
            ]
        
        if email:
            filtered_users = [
                user for user in filtered_users
                if email.lower() in user.email.lower()
            ]
        
        if username:
            filtered_users = [
                user for user in filtered_users
                if username.lower() in user.username.lower()
            ]
        
        return filtered_users
    


    def _filter_users_by_ticket_stats(
            self,
            users: list[UserWithTicketStats],
            stauses: Optional[list[str]] = None
    ) -> list[UserWithTicketStats]:
        
        """Filter users based on ticket statistics."""
        if not stauses:
            return users
        
        status_field_map = {
            "resolved": "resolved",
            "pending": "pending",
            "assigned_open": "assigned_open",
            "in_progress": "in_progress",
            "approval_pending": "approval_pending",
            "approved": "approved",
        }

        # Filter users who have tickets in at least one of the specified statuses
        filtered_users = []
        # ✔ Prevents duplicates
        # ✔ Makes the filtering accurate
        # ✔ Improves performance for large lists
        seen_user_ids = set()

        for user in users:
            # Skip if user already added
            if user.user_id in seen_user_ids:
                continue
            for status in stauses:
                status_lower = status.lower()
                if status_lower in status_field_map:
                    stat_field = status_field_map[status_lower]
                    if getattr(user, stat_field, 0) > 0:
                        filtered_users.append(user)
                        seen_user_ids.add(user.user_id)
                        break
        return filtered_users




    async def get_users_with_stats(
            self,
            session: AsyncSession,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            roles : Optional[list[str]] = None,
            full_name: Optional[str] = None,
            email: Optional[str] = None,
            username: Optional[str] = None,
            stauses: Optional[list[str]] = None,

    ) -> UsersWithStatsResponse:
        """Get all users with their ticket statistics."""

        # Step 1: Get users with stats (all users or filtered by roles)
        if roles is None:
            users_with_stats = await self._get_all_users_with_stats(
                session, start_date, end_date
            )
        else:
            users_with_stats = await self._get_users_by_role_with_stats(
                session, roles, start_date, end_date
            )
        
        # Step 2: Apply profile filters (full_name, email, username)
        filtered_users = self._filter_users_by_profile_field(
            users_with_stats, full_name, email, username
        )

        # Step 3: Apply ticket status filters
        filtered_users = self._filter_users_by_ticket_stats(
            filtered_users, stauses
        )

        return UsersWithStatsResponse(
            users=filtered_users,
            start_date=start_date,
            end_date=end_date
        )
        