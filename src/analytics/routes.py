from fastapi import APIRouter, Depends, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import AnalyticsService
from src.auth.dependencies import role_checker
from src.db.main import get_session
from src.db.models import User
from typing import Optional
from datetime import datetime
from uuid import UUID



analytics_router = APIRouter()
analytics_service = AnalyticsService()
AnalyticsAccess = Depends(role_checker(["admin", "manager", "it_support"]))


@analytics_router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    dependencies=[AnalyticsAccess],
    summary="Get analytics dashboard data",
)
async def get_analytics_dashboard(
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
):
    return await analytics_service.get_analytics_dashboard(
        session=session,
        page=page,
        page_size=page_size
    )

@analytics_router.get(
    "/detail-stats",
    status_code=status.HTTP_200_OK,
    dependencies=[AnalyticsAccess],
    summary="Get support metrics based on user roles and user",
)
async def get_support_metrics(
    session: AsyncSession = Depends(get_session),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering metrics"),
    user_id: Optional[UUID] = Query(None, description="User ID to filter metrics"),
    roles: Optional[list[str]] = Query(
        None,
        description="List of user roles to filter metrics (e.g., admin, it_support, manager)"
    ),
):
    return await analytics_service.SupportMetricsService(
        session=session,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        roles=roles
    )


@analytics_router.get(
    "/users-with-stats",
    status_code=status.HTTP_200_OK,
    dependencies=[AnalyticsAccess],
    summary="Get users with ticket statistics",
)
async def get_users_with_stats(
    session: AsyncSession = Depends(get_session),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering metrics"),
    roles: Optional[list[str]] = Query(
        None,
        description="List of user roles to filter (e.g., admin, it_support, manager). If not provided, returns all users."
    ),
    full_name: Optional[str] = Query(None, description="Filter users by full name (case-insensitive partial match)"),
    email: Optional[str] = Query(None, description="Filter users by email (case-insensitive partial match)"),
    username: Optional[str] = Query(None, description="Filter users by username (case-insensitive partial match)"),
    stauses: Optional[list[str]] = Query(
        None,
        description="Filter users by ticket statuses. Select one or more: 'resolved', 'pending', 'assigned_open', 'in_progress'. Returns users who have tickets in any of the selected statuses."
    ),
):
    return await analytics_service.get_users_with_stats(
        session=session,
        start_date=start_date,
        end_date=end_date,
        roles=roles,
        full_name=full_name,
        email=email,
        username=username,
        stauses=stauses
    )