from fastapi import APIRouter, Depends, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import AnalyticsService
from src.auth.dependencies import role_checker
from src.db.main import get_session
from src.db.models import User



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


