from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from uuid import UUID

from src.db.models.ticket import Ticket, TicketStatus, TicketPriority
from src.db.models.user import User
from src.ticket.schemas import TicketCreateRequest, TicketUpdateRequest
from src.errors import TicketNotFoundError, UserNotFoundError, UnauthorizedError, InvalidTicketUpdateError, TicketPriorityUpdateError, TicketStatusUpdateError, TicketAssignmentError, BadRequestError


PRIVILEGED_ROLES = {"admin", "manager", "it_support"}
def is_privileged(user: User) -> bool:
    """Check if the user has a privileged role."""
    return user.role.value.lower() in PRIVILEGED_ROLES


class TicketService:

    # ==================== Helper Methods ====================
    async def get_ticket(
            self,
            ticket_id : UUID,
            session : AsyncSession
    ) -> Ticket:
        ticket = (await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )).scalar_one_or_none()

        if not ticket:
            raise TicketNotFoundError()
        return ticket
    


    async def get_user(
            self,
            user_id : UUID,
            session : AsyncSession
    ) -> User:
        user = (await session.execute(
            select(User).where(User.user_id == user_id)
        )).scalar_one_or_none()

        if not user:
            raise UserNotFoundError()
        return user
    



    async def authorize_user(
            self,
            user_id : UUID,
            session : AsyncSession
    ) -> User:
        user = await self.get_user(user_id, session)
        if not is_privileged(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Assigned user must have role {', '.join(PRIVILEGED_ROLES)}."
            )
        return user
    



    def check_ticket_access(
            self,
            ticket : Ticket,
            user : User,
            user_id : UUID,
    ) -> bool:
        has_access = (
            is_privileged(user) or
            str(ticket.created_by) == str(user_id) or
            (ticket.assigned_to and str(ticket.assigned_to) == str(user_id))
        )
        if not has_access:
            raise UnauthorizedError()
        return has_access
    



    def validate_ticket_update_permission(
            self,
            update_data: dict,
            user: User,
            ticket: Ticket,
            user_id : UUID
    ):
        is_creator = str(ticket.created_by) == str(user_id)
        user_is_privileged = is_privileged(user)

        basic_fields = {
            "subject", "description", "types_of_issue"
        }
        if any(fields in update_data for fields in basic_fields) and not (is_creator or user_is_privileged):
            raise InvalidTicketUpdateError()
        
        if "priority" in update_data and not user_is_privileged:
            raise TicketPriorityUpdateError()
        
        if "status" in update_data and not user_is_privileged:
            raise TicketStatusUpdateError()
        
        if "assigned_to" in update_data and not (is_creator or is_privileged):
            raise TicketAssignmentError()
        


        
    def check_delete_permission(
            self,
            ticket : Ticket,
            user : User,
            user_id : UUID
    ):
        if ticket.created_by != user_id and not is_privileged(user):
            raise UnauthorizedError()
        

        # ==================== Main Service Methods ====================

    async def create_ticket(
            self,
            ticket_data : TicketCreateRequest,
            user_id : UUID,
            session : AsyncSession,
    ):
        # Create ticket instance
        new_ticket = Ticket(
            subject=ticket_data.subject,
            description=ticket_data.description,
            priority=ticket_data.priority,
            types_of_issue=ticket_data.types_of_issue,
            status=TicketStatus.OPEN,
            created_by=user_id,
        )
        if ticket_data.assigned_to:
            await self.authorize_user(ticket_data.assigned_to, session)
            new_ticket.assigned_to = ticket_data.assigned_to

        session.add(new_ticket)
        await session.commit()
        await session.refresh(new_ticket)
        return new_ticket
    

    
    async def get_user_ticket(
            self,
            ticket_id: UUID,
            user_id : UUID,
            session: AsyncSession,
    ):
        ticket = await self.get_ticket(ticket_id,session)
        user = await self.get_user(user_id,session)

        has_access = self.check_ticket_access(ticket, user, user_id)
        if not has_access:
            raise UnauthorizedError()
        return ticket
    


    async def get_user_tickets(
            self,
            user_id : UUID,
            session : AsyncSession
    ):
        user_tickets = select(Ticket).where(
            (Ticket.created_by == user_id) | (Ticket.assigned_to == user_id)
        )
        result = await session.execute(user_tickets)
        tickets = result.scalars().all()
        if not tickets:
            raise TicketNotFoundError()
        return tickets
    



    async def update_ticket(
            self,
            ticket_id : UUID,
            ticket_data : TicketUpdateRequest,
            user_id : UUID,
            session : AsyncSession
    ) -> Ticket:
        ticket = await self.get_ticket(ticket_id, session)
        user = await self.get_user(user_id, session)

        update_data = ticket_data.model_dump(exclude_unset=True)
        if not update_data:
            raise BadRequestError("No fields provided for update.")
        
        # Validate permissions for the fields being updated
        self.validate_ticket_update_permission(update_data,user,ticket,user_id)

        # Validate assigned_to user if being updated
        if "assigned_to" in update_data and update_data["assigned_to"] is not None:
            await self._validate_user_for_assignment(update_data["assigned_to"], session)

        
        # Apply updates
        for field, value in update_data.items():
            setattr(ticket, field, value)

        ticket.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(ticket)
        return ticket
    



    async def delete_ticket(
            self,
            ticket_id : UUID,
            user_id : UUID,
            session : AsyncSession
    ):
        ticket = await self.get_ticket(ticket_id,session)
        user = await self.get_user(user_id, session)

        self.check_delete_permission(ticket,user,user_id)

        await session.delete(ticket)
        await session.commit()
        return None



