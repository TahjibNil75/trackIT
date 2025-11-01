from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from .service import TicketService, TicketCreateRequest, TicketUpdateRequest, TicketStatus
from .schemas import TicketDetails, TicketResponse
from src.auth.dependencies import role_checker, AccessTokenBearer
from src.db.main import get_session
from src.db.models import User, UserRole


ticket_router = APIRouter()
ticket_service = TicketService()

AllUsers = Depends(role_checker(["user", "manager", "it_support", "admin"]))
PrivilegedRoles = Depends(role_checker(["admin", "manager", "it_support"]))


@ticket_router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketDetails,
    dependencies=[AllUsers],
    summary="Create a new ticket",
)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]
    return await ticket_service.create_ticket(ticket_data, user_id, session)


@ticket_router.patch(
    "/update/{ticket_id}",
    status_code=status.HTTP_200_OK,
    response_model=TicketResponse,
    dependencies=[AllUsers],
)
async def update_ticket(
    ticket_id: UUID,
    ticket_data: TicketUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]
    return await ticket_service.update_ticket(ticket_id, ticket_data, user_id, session)


@ticket_router.get(
    "/my-tickets",
    status_code=status.HTTP_200_OK,
    response_model=list[TicketDetails],
    dependencies=[AllUsers],
)
async def get_my_tickets(
    session : AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]
    return await ticket_service.get_user_tickets(user_id, session)

@ticket_router.get(
        "/{ticket_id}",
        status_code=status.HTTP_200_OK,
        response_model=TicketDetails,
        dependencies=[AllUsers]
)
async def get_ticket_by_id(
    ticket_id: UUID,
    session : AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    
    """
    Access to specific ticket is granted if:
    - User is admin, manager, or IT support (can see any ticket)
    - User created the ticket
    - User is assigned to the ticket
    """

    user_id = current_user["user"]["user_id"]
    return await ticket_service.get_user_ticket(ticket_id,user_id,session)



@ticket_router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AllUsers],
)
async def delete_ticket(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"] 
    return await ticket_service.delete_ticket(ticket_id, user_id, session)
