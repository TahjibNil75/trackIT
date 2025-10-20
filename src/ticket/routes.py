from fastapi import APIRouter, Depends, status, HTTPException
from .service import TicketService, TicketCreateRequest
from src.auth.dependencies import role_checker, AccessTokenBearer
from .schemas import TicketDetails
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session




ticket_router = APIRouter()
ticket_service = TicketService()


AllUsers = Depends(role_checker(
    ["user", "manager", "it_support", "admin"]
))



@ticket_router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model= TicketDetails,
    dependencies=[AllUsers]
)
async def create_ticket(
    ticket_data : TicketCreateRequest,
    session : AsyncSession = Depends(get_session),
    token_details: dict = Depends(AccessTokenBearer()),
):
    user_id = token_details["user"]["user_id"]
    return await ticket_service.create_ticket(ticket_data, user_id,session)
    