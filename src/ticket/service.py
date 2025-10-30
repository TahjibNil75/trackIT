from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from uuid import UUID

from src.db.models.ticket import Ticket, TicketStatus, TicketPriority
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
    
    
    async def get_ticket_by_id(
    self,
    ticket_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> Ticket:
    # Fetch ticket
        ticket = (await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )).scalar_one_or_none()

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Fetch user
        user = (await session.execute(
            select(User).where(User.user_id == user_id)
        )).scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check access permissions
        # Access granted if:
        #     - user is admin", "manager", "it_support" OR
        #     - user created the ticket OR
        #     - ticket has an assignee AND user is that assignee
        privileged_roles = {"admin", "manager", "it_support"}
        has_access = (
            user.role.value.lower() in privileged_roles or
            str(ticket.created_by) == str(user_id) or
            (ticket.assigned_to and str(ticket.assigned_to) == str(user_id))
        )

        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this ticket."
            )

        return ticket


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
    
    async def delete_ticket(
            self,
            ticket_id: UUID,
            session: AsyncSession,
            user_id: UUID,
    ):
        # Fetch ticket
        statement = select(Ticket).where(Ticket.ticket_id == ticket_id)
        ticket = (await session.execute(statement)).scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found."
            )
        
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        allowed_roles = ["admin", "manager", "it_support"]

        if str(ticket.created_by) != str(user_id) and user.role.value.lower() not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this ticket."
            )
        await session.delete(ticket)
        await session.commit()
        return None
    
    async def assign_ticket(
        self,
        ticket_id: UUID,
        assigned_to: UUID,
        current_user: User,
        session: AsyncSession,
    ) -> Ticket:
        ticket_statement = select(Ticket).where(Ticket.ticket_id == ticket_id)
        ticket = (await session.execute(ticket_statement)).scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found."
            )

        allowed_roles = ["admin", "manager", "it_support"]
        is_creator = UUID(str(ticket.created_by)) == UUID(str(current_user.user_id))
        has_allowed_role = current_user.role.value.lower() in allowed_roles

        if not (is_creator or has_allowed_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to assign this ticket."
            )

        user_stmt = select(User).where(User.user_id == assigned_to)
        assigned_user = (await session.execute(user_stmt)).scalar_one_or_none()

        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found."
            )

        ticket.assigned_to = assigned_to
        await session.commit()
        await session.refresh(ticket)
        return ticket
    
    async def self_assign(
            self,
            ticket_id : UUID,
            user_id : UUID,
            session : AsyncSession,
    ) -> Ticket:
        ticket = (await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )).scalar_one_or_none()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tickets Not Found"
            )
        

        user = (await session.execute(
            select(User).where(User.user_id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not found"
            )
        
        priviledged_roles = {"admin", "manager", "it_support"}
        if user.role.value.lower() not in priviledged_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are now allowed to perform this action"
            )
        
        ticket.assigned_to = user_id
        await session.commit()
        await session.refresh(ticket)
        return ticket
        
    
    async def update_ticket_status(
            self,
            ticket_id : UUID,
            user_id : UUID,
            new_status : TicketStatus, # ✔ enum, not Pydantic model
            session : AsyncSession,
    ) -> Ticket:
        ticket = (await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )).scalar_one_or_none()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket Not found"
            )
        
        user = (await session.execute(
            select(User).where(User.user_id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        user_role = user.role.value.lower()
        allowed_statuses = None
        if user_role == "manager":
            allowed_statuses = {
                TicketStatus.APPROVAL_PENDING,
                TicketStatus.APPROVED
            }

        if allowed_statuses and new_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update ticket status."
            )
        elif user_role not in ["admin", "it_support"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update ticket status."
            )


        ticket.status = new_status
        await session.commit()
        await session.refresh(ticket)
        return ticket
    
    async def update_ticket_priority(
            self,
            ticket_id : UUID,
            user_id : UUID,
            new_priority : TicketPriority,
            session : AsyncSession

    )-> Ticket:
        
        ticket = (await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )).scalar_one_or_none()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket Not found"
            )
        
        user = (await session.execute(
            select(User).where(User.user_id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        user_role = user.role.value.lower()
        if user_role not in ["admin", "it_support", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update ticket status."
            )
        
        ticket.priority = new_priority
        await session.commit()
        await session.refresh(ticket)
        return ticket
        

        




