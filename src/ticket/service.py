from .schemas import TicketCreateRequest
import uuid
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models.ticket import Ticket, TicketStatus
from src.db.models.user import User, UserRole
from typing import Optional


class TicketService:
    async def create_ticket(
        self,
        ticket_data: TicketCreateRequest,
        user_id: uuid.UUID,
        session: AsyncSession,
    ):
        ticket_data_dict = ticket_data.model_dump()
        new_ticket = Ticket(**ticket_data_dict)
        new_ticket.created_by = user_id
        new_ticket.status = TicketStatus.OPEN

        session.add(new_ticket)
        await session.commit()
        await session.refresh(new_ticket)
        return new_ticket

    async def validate_assigne(
        self,
        assignee_id: uuid.UUID,
        session: AsyncSession,
    ) -> tuple[bool, Optional[str]]:
        user = await session.get(User, assignee_id)
        if not user:
            return False, "Assignee does not exist."
        if user.role not in [UserRole.ADMIN, UserRole.IT_SUPPORT, UserRole.MANAGER]:
            return False, "Assignee must have a role of Admin, IT Support, or Manager."
        return True, None
