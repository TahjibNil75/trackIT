from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from uuid import UUID

from src.db.models.ticket import Ticket, TicketStatus
from src.db.models.user import User
from src.ticket.schemas import TicketCreateRequest, TicketUpdateRequest


class TicketService:
    async def create_ticket(
        self,
        ticket_data: TicketCreateRequest,
        user_id: UUID,
        session: AsyncSession,
    ) -> Ticket:

        new_ticket = Ticket(
            subject=ticket_data.subject,
            description=ticket_data.description,
            priority=ticket_data.priority,
            types_of_issue=ticket_data.types_of_issue,
            status=TicketStatus.OPEN,
            created_by=user_id,
        )

        # Validate assignment
        if ticket_data.assigned_to:
            statement = select(User).where(User.user_id == ticket_data.assigned_to)
            assigned_user_result = await session.exec(statement)
            assigned_user = assigned_user_result.first()

            if not assigned_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned user not found."
                )

            if assigned_user.role.value not in ["ADMIN", "MANAGER", "IT_SUPPORT"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Assigned user must have role ADMIN, MANAGER, or IT_SUPPORT."
                )

            new_ticket.assigned_to = ticket_data.assigned_to

        session.add(new_ticket)
        await session.commit()
        await session.refresh(new_ticket)
        return new_ticket


    async def update_ticket(
        self,
        ticket_id: UUID,
        ticket_data: TicketUpdateRequest,
        session: AsyncSession,
        user_id: UUID,   # ✅ just user_id now
    ) -> Ticket:
        # Fetch ticket
        statement = select(Ticket).where(Ticket.ticket_id == ticket_id)
        ticket = (await session.execute(statement)).scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found."
            )

        if UUID(str(ticket.created_by)) != UUID(str(user_id)):   ## Need To fix it
            raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to update this ticket."
    )

        # Apply updates
        update_data = ticket_data.model_dump(exclude_unset=True)
        for field in ["subject", "description", "priority", "types_of_issue", "assigned_to"]:
            if field in update_data:
                setattr(ticket, field, update_data[field])

        # Set status to OPEN by default on update
        ticket.status = TicketStatus.OPEN

        await session.commit()
        await session.refresh(ticket)
        return ticket
    
    async def get_user_tickets(
            self,
            user_id: UUID,
            session: AsyncSession,
    ):
        statement = select(Ticket).where(
            (Ticket.created_by == user_id) | (Ticket.assigned_to == user_id)
        )
        result = await session.execute(statement)
        tickets = result.scalars().all()   # ✅ FIXED
        return tickets
    

