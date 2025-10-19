from .schemas import TicketCreateRequest, TicketUpdateRequest
import uuid
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models.ticket import Ticket, TicketStatus
from src.db.models.user import User, UserRole
from typing import Optional
from sqlmodel import select, desc, delete


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
    
    async def get_ticket(
            self,
            ticket_id : uuid.UUID,
            session : AsyncSession,

    ):
        statement = select(Ticket).where(Ticket.ticket_id == ticket_id)
        result = await session.execute(statement)
        # ticket = result.first()  # returns Row object, not Ticket
        ticket = result.scalar_one_or_none()  # fix: ✅ returns Ticket instance
        return ticket if ticket is not None else None
    
    async def delete_ticket(
            self,
            ticket_id : uuid.UUID,
            session : AsyncSession
    ):
        ticket = await self.get_ticket(ticket_id, session)
        if not ticket:
            return None
        
        await session.delete(ticket)
        await session.commit()
        return True
    
    async def update_ticket(
            self,
            ticket_id : uuid.UUID,
            ticket_data : TicketUpdateRequest,
            session : AsyncSession,
    ):
        ticket = await self.get_ticket(ticket_id, session)
        if not ticket:
            return None
        
        ticket_data_dict = ticket_data.model_dump(exclude_unset=True) # exclude_unset=True it tells Pydantic to only include the fields that the user actually provided in the update request —not all fields from the model definition.
        ticket.sqlmodel_update(ticket_data_dict)
        await session.commit()
        await session.refresh(ticket)
        return ticket
    
    async def check_user_permission(
            self,
            user : User,
            ticket_id : uuid.UUID,
            session : AsyncSession,
    ):
        ticket = await self.get_ticket(ticket_id, session)
        if not ticket:
            # return False, "Ticket not found."  # ❌ returns string instead of ticket object
            return False, None # ✅ return None for ticket object if not found
        
        if ticket.created_by == user.user_id:
            return True, ticket # ✅ return actual ticket object
        if user.role in [UserRole.ADMIN, UserRole.IT_SUPPORT, UserRole.MANAGER]:
            return True, ticket # ✅ same here
        
        return False, "You do not have permission to modify this ticket."
    
    async def can_view_ticket(
            self, 
            user : User,
            ticket : Ticket
    ) -> bool:
        if ticket.created_by == user.user_id:
            return True
        if user.role in [UserRole.ADMIN, UserRole.IT_SUPPORT, UserRole.MANAGER]:
            return True
        
        return False
        
    async def get_user_tickets(
            self,
            user_id : uuid.UUID,
            session : AsyncSession,
            skip : int = 0,
            limit : int = 10,
    ):
        statement = (
            select(Ticket)
            .where(Ticket.created_by == user_id)
            .order_by(desc(Ticket.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(statement)
        tickets = result.scalars().all()
        return tickets

    


