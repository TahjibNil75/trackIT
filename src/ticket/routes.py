from fastapi import APIRouter, Depends, status, Query
from .service import TicketService
from .schemas import TicketCreateRequest, TicketResponse, TicketUpdateRequest, TicketDetails
from src.auth.dependencies import get_current_user
from src.db.models.user import User
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from fastapi.exceptions import HTTPException
import uuid
from typing import List



ticket_router = APIRouter()
ticket_service = TicketService()


# ==================== TICKET OPERATIONS ====================
@ticket_router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketResponse,
)
async def create_ticket(
    ticket_data : TicketCreateRequest,
    current_user : User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session) # ← This handles token authentication
):
    # If user wants to assign ticket, validate the assignee
    if ticket_data.assigned_to:
        is_valid, error_message = await ticket_service.validate_assigne(
            ticket_data.assigned_to,
            session
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
    new_ticket = await ticket_service.create_ticket(
        ticket_data,
        current_user.user_id,
        session
    )
    return new_ticket



@ticket_router.put(
    "/{ticket_id}/update",
    status_code=status.HTTP_200_OK,
    response_model=TicketResponse,
)
async def update_ticket(
    ticket_id : uuid.UUID,
    ticket_data : TicketUpdateRequest,
    current_user : User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)
):
    
    has_permission, ticket = await ticket_service.check_user_permission(
        current_user,
        ticket_id,
        session
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found."
        )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this ticket."
        )    
    
    if ticket_data.assigned_to:
        is_valid, error_message = await ticket_service.validate_assigne(
            ticket_data.assigned_to,
            session
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
    update_ticket = await ticket_service.update_ticket(
        ticket_id,
        ticket_data,
        session,
    )
    return update_ticket
    


@ticket_router.get(
    "/{ticket_id}",
    response_model=TicketDetails,
    status_code=status.HTTP_200_OK,
)
async def get_ticket_by_id(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)   
):
    # ✅ Fixed: removed current_user parameter
    ticket = await ticket_service.get_ticket(ticket_id, session)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket Not Found"
        )
    
    can_view = await ticket_service.can_view_ticket(current_user, ticket)
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this ticket"
        )
    
    return ticket


# Get MY tickets (current logged-in user)
@ticket_router.get(
    "/user/my-ticekts",
    response_model= List[TicketDetails],
    status_code=status.HTTP_200_OK,
)
async def get_my_tickets(
    skip : int = Query(0, ge=0, description="Number of Tickets to skip"),
    limit : int = Query(10, ge = 1, le = 100, description="Max number of tickets to return"),
    session : AsyncSession = Depends(get_session),
    current_user : User = Depends(get_current_user),
):
    all_tickets = await ticket_service.get_user_tickets(
        current_user.user_id,
        session,
        skip,
        limit,
    )
    return all_tickets

# ##
# # Get first 10 tickets
# GET /api/v1/tickets/user/my-tickets

# # Get next 10 tickets (pagination)
# GET /api/v1/tickets/user/my-tickets?skip=10&limit=10

# # Get 20 tickets
# GET /api/v1/tickets/user/my-tickets?limit=20

@ticket_router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_my_ticket(
    ticket_id : uuid.UUID,
    session : AsyncSession = Depends(get_session),
    current_user : User = Depends(get_current_user)
):
    """
    Delete a ticket created by the current user.
    
    Regular users can only delete their own tickets.
    Admins/Managers/IT Support can delete any ticket.
    """

    has_permission, ticket_or_message = await ticket_service.check_user_permission(
    current_user,
    ticket_id,
    session
)

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permissions to delete this ticekt"
        )
    
    if ticket_or_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    delete_ticket = await ticket_service.delete_ticket(ticket_id, session)

    if not delete_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket Not Found"
        )
    
    return None
