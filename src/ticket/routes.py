from fastapi import APIRouter, Depends, status
from .service import TicketService
from .schemas import TicketCreateRequest, TicketResponse, TicketUpdateRequest
from src.auth.dependencies import get_current_user
from src.db.models.user import User
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from fastapi.exceptions import HTTPException
import uuid



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
    