from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.db.models.ticket import Ticket, TicketStatus
from src.db.models.user import User
from src.ticket.schemas import TicketCreateRequest

class TicketService:
    async def create_ticket(
        self,
        ticket_data: TicketCreateRequest,
        user_id: str,
        session: AsyncSession,
    ) -> Ticket:

        # Initialize ticket without ticket_id (default factory will handle it)
        new_ticket = Ticket(
            subject=ticket_data.subject,
            description=ticket_data.description,
            priority=ticket_data.priority,
            types_of_issue=ticket_data.types_of_issue,
            status=TicketStatus.OPEN, 
            created_by=user_id,
        )

        # Handle assignment
        if ticket_data.assigned_to:
            stmt = select(User).where(User.user_id == ticket_data.assigned_to)
            assigned_user_result = await session.exec(stmt)
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
            # new_ticket.assigned_at = datetime.utcnow()  # optional field if exists

        session.add(new_ticket)
        await session.commit()
        await session.refresh(new_ticket)

        return new_ticket
