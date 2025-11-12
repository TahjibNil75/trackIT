from fastapi import APIRouter, Depends, status, File, UploadFile,Form
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from .service import TicketService, TicketCreateRequest, TicketUpdateRequest, TicketStatus
from .schemas import TicketDetails, TicketResponse, TicketSummaryResponse
from src.auth.dependencies import role_checker, AccessTokenBearer
from src.db.main import get_session
from src.db.models import User, UserRole
from typing import Optional
import json


ticket_router = APIRouter()
ticket_service = TicketService()

AllUsers = Depends(role_checker(["user", "manager", "it_support", "admin"]))
PrivilegedRoles = Depends(role_checker(["admin", "manager", "it_support"]))


@ticket_router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketResponse,
    dependencies=[AllUsers],
    summary="Create a new ticket",
)
# async def create_ticket(
#     ticket_data: TicketCreateRequest,
#     session: AsyncSession = Depends(get_session),
#     current_user: dict = Depends(AccessTokenBearer()),
# ):
#     user_id = current_user["user"]["user_id"]
#     return await ticket_service.create_ticket(ticket_data, user_id, session)

async def create_ticket(
    subject: str = Form(..., min_length=5, max_length=200),
    description: str = Form(..., min_length=10),
    types_of_issue: str = Form(...),
    priority: str = Form(default="medium"),
    assigned_to: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]
    ticket_dict = {
        "subject": subject,
        "description": description,
        "types_of_issue": types_of_issue,
        "priority": priority,
    }

    if assigned_to is not None:
        ticket_dict["assigned_to"] = UUID(assigned_to) if assigned_to else None

    ticket_object = TicketCreateRequest(**ticket_dict)

    return await ticket_service.create_ticket_with_attachments(
        ticket_object,
        user_id,
        files,
        session
    )


@ticket_router.patch(
    "/update/{ticket_id}",
    status_code=status.HTTP_200_OK,
    response_model=TicketResponse,
    dependencies=[AllUsers],
)
# async def update_ticket(
#     ticket_id: UUID,
#     ticket_data: TicketUpdateRequest,
#     session: AsyncSession = Depends(get_session),
#     current_user: dict = Depends(AccessTokenBearer()),
# ):
#     user_id = current_user["user"]["user_id"]
#     return await ticket_service.update_ticket(ticket_id, ticket_data, user_id, session)

async def update_ticket(
    ticket_id: UUID,
    subject: Optional[str] = Form(None, min_length=5, max_length=200),
    description: Optional[str] = Form(None, min_length=10),
    types_of_issue: Optional[str] = Form(None),
    priority: Optional[str] = Form(None),
    status_field: Optional[str] = Form(None, alias="status"),
    assigned_to: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]

    # Build update dict with only provided fields
    ticket_dict = {}
    if subject is not None:
        ticket_dict["subject"] = subject
    if description is not None:
        ticket_dict["description"] = description
    if types_of_issue is not None:
        ticket_dict["types_of_issue"] = types_of_issue
    if priority is not None:
        ticket_dict["priority"] = priority
    if status_field is not None:
        ticket_dict["status"] = status_field
    if assigned_to is not None:
        ticket_dict["assigned_to"] = UUID(assigned_to) if assigned_to else None

    ticket_object = TicketUpdateRequest(**ticket_dict)

    return await ticket_service.update_ticket_with_attachments(
        ticket_id=ticket_id,
        ticket_data=ticket_object,
        files=files,
        user_id=user_id,
        session=session
    )


@ticket_router.get(
    "/my-tickets",
    status_code=status.HTTP_200_OK,
    response_model=list[TicketSummaryResponse],
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


@ticket_router.delete(
    "/attachment/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AllUsers],
)
async def delete_attachment(
    attachment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]
    return await ticket_service.delete_attachment(attachment_id, user_id, session)