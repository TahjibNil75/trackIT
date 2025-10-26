from fastapi import APIRouter, Depends, status, Query
from .service import UserManagementService
from src.auth.dependencies import role_checker, AccessTokenBearer
from .schemas import UserRole, UserRoleUpdateRequest, UserStatusUpdateRequest, UserListResponse

from src.db.main import get_session


user_management_router = APIRouter()
user_management_service = UserManagementService()
AdminOnly = Depends(role_checker(["admin"]))
AllUsers = Depends(role_checker(["user", "manager", "it_support", "admin"]))


@user_management_router.put(
    "/update-role/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[AdminOnly],
)
async def update_user_role(
    user_id: str,
    new_role: UserRoleUpdateRequest,
    session = Depends(get_session)
):
    return await user_management_service.update_user_role(
        user_id=user_id,
        new_role= new_role.role,
        session=session
    )

@user_management_router.get(
    "/all-users",
    response_model = UserListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[AllUsers],
)
async def list_all_users(
    page : int = Query(1, ge=1),
    page_size : int = Query(10, ge=1, le=100),
    is_active : bool | None = None,
    session = Depends(get_session)
):
    return await user_management_service.list_all_users(
        session=session,
        page=page,
        page_size=page_size,
        is_active=is_active
    )

@user_management_router.get(
    "/users-by-role/{role}",
    response_model = UserListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[AllUsers],
)
async def list_users_by_role(
    role : UserRole,
    page : int = Query(1, ge=1),
    page_size : int = Query(10, ge=1, le=100),
    session = Depends(get_session)
):
    return await user_management_service.list_all_users(
        session=session,
        page=page,
        page_size=page_size,
        role=role
)
