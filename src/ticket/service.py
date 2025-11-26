from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from uuid import UUID

from src.db.models.ticket import Ticket, TicketStatus, TicketPriority
from src.db.models.user import User, UserRole
from src.ticket.schemas import TicketCreateRequest, TicketUpdateRequest
from src.errors import TicketNotFoundError, UserNotFoundError, UnauthorizedError, InvalidTicketUpdateError, TicketPriorityUpdateError, TicketStatusUpdateError, TicketAssignmentError, BadRequestError, AttachmentNotFoundError

from sqlalchemy.orm import selectinload  ## required for fetching comments
from src.db.models.comment import Comment
from fastapi import UploadFile
from src.utils.s3_utils import upload_file_to_s3
from src.db.models.attachment import Attachment
from src.db.models.ticket_history import TicketHistory

from typing import Optional




HISTORY_PAGE_SIZE = 10



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
    



    async def authorize_user( ## Fix: get authorize user
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

        basic_fields = {"subject", "description", "types_of_issue"}
        if any(field in update_data for field in basic_fields) and not (is_creator or user_is_privileged):
            raise InvalidTicketUpdateError()
        
        if "priority" in update_data and update_data["priority"] != ticket.priority and not user_is_privileged:
            raise TicketPriorityUpdateError()
        
        if "status" in update_data and update_data["status"] != ticket.status and not user_is_privileged:
            raise TicketStatusUpdateError()
        
        if "assigned_to" in update_data and not (is_creator or is_privileged(user)):
            raise TicketAssignmentError()

    async def _validate_user_for_assignment(self, user_id, session):
        """
        Validate if the assigned_to user exists and has the correct role.
        """
        if not user_id:
            return  # No assignment change → nothing to validate

        # Fetch user
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Assigned user does not exist")

        # Allowed roles
        valid_roles = {
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.IT_SUPPORT
        }

        if user.role not in valid_roles:
            raise ValueError(
                f"User role '{user.role}' is not allowed to be assigned to tickets"
            )


        
    def check_delete_permission(
            self,
            ticket : Ticket,
            user : User,
            user_id : UUID
    ):
        if ticket.created_by != user_id and not is_privileged(user):
            raise UnauthorizedError()
        

    async def get_attachment(
            self,
            attachment_id : UUID,
            session : AsyncSession
    ) -> Attachment:
        attachment = (await session.execute(
            select(Attachment).where(Attachment.attachment_id == attachment_id)
        )).scalar_one_or_none()
        if not attachment:
            raise AttachmentNotFoundError()
        return attachment
    

    async def log_ticket_history(
            self,
            ticket_id : UUID,
            action_type : str,
            old_value : Optional[str],
            new_value : Optional[str],
            changed_by : UUID,
            session : AsyncSession
    ):
        history_entry = TicketHistory(
            ticket_id=ticket_id,
            action_type=action_type,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            changed_at=datetime.utcnow()
        )
        session.add(history_entry)
        await session.commit()
        await session.refresh(history_entry)
        return history_entry
        
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

        # Log ticket creation in history
        await self.log_ticket_history(
            ticket_id=new_ticket.ticket_id,
            action_type="created",
            old_value=None,
            new_value=f"Ticket created with status: {new_ticket.status.value}",
            changed_by=user_id,
            session=session
        )

        return new_ticket
    



    async def get_user_ticket(
        self,
        ticket_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ):
        result = await session.execute(
            select(Ticket)
            .options(selectinload(Ticket.comments))  # eager-load comments
            .where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise TicketNotFoundError()

        user = await self.get_user(user_id, session)
        self.check_ticket_access(ticket, user, user_id)
        
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
        # for field, value in update_data.items():
        #     setattr(ticket, field, value)

        for field, value in update_data.items():
            old_value = str(getattr(ticket, field))
            setattr(ticket, field, value)
            new_value = str(value)
            if old_value != new_value:
                await self.log_ticket_history(
                    ticket_id=ticket.ticket_id,
                    action_type=f"{field}_changed",
                    old_value=old_value,
                    new_value=new_value,
                    changed_by=user_id,
                    session=session
                )

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
    
    async def attach_files_to_ticket(
    self,
    ticket: Ticket,
    files: list[UploadFile],
    session: AsyncSession,
):
        attachments_list = []  

        for file in files:
            file_url = await upload_file_to_s3(file)
            attachment = Attachment(
                ticket_id=ticket.ticket_id,
                file_name=file.filename,
                file_url=file_url,
                file_type=file.content_type,
            )
            session.add(attachment)
            attachments_list.append(attachment)

        await session.commit()
        return attachments_list

    
    async def create_ticket_with_attachments(
            self,
            ticket_data : TicketCreateRequest,
            user_id : UUID,
            files : Optional[list[UploadFile]],
            session : AsyncSession,
    ):
        ticket = await self.create_ticket(ticket_data, user_id, session)
        if files:
            await self.attach_files_to_ticket(ticket, files, session)

        result = await session.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.attachments),
            )
            .where(Ticket.ticket_id == ticket.ticket_id)
        )

        ticket = result.scalar_one()
        return ticket
    
    async def update_ticket_with_attachments(
            self,
            ticket_id : UUID,
            ticket_data : TicketUpdateRequest,
            user_id : UUID,
            files : Optional[list[UploadFile]],
            session : AsyncSession
    ) -> Ticket:
        ticket = await self.update_ticket(ticket_id, ticket_data, user_id, session)
        if files:
            await self.attach_files_to_ticket(ticket, files, session)

        # Reload ticket with attachments
        result = await session.execute(
            select(Ticket)
            .options(selectinload(Ticket.attachments))
            .where(Ticket.ticket_id == ticket.ticket_id)
        )

        ticket = result.scalar_one()
        return ticket
    

    async def delete_attachment(
            self,
            attachment_id : UUID,
            user_id : UUID,
            session : AsyncSession
    ):
        attachment = await self.get_attachment(attachment_id, session)
        ticket = await self.get_ticket(attachment.ticket_id, session)
        user = await self.get_user(user_id, session)

        is_creator = str(ticket.created_by) == str(user_id)
        user_is_admin = user.role.value.lower() == "admin"
        if not (is_creator or user_is_admin):
            raise UnauthorizedError()
        
        await session.delete(attachment)
        await session.commit()
    
    # async def get_ticket_history(
    #         self,
    #         ticket_id : UUID,
    #         user_id : UUID,
    #         session : AsyncSession
    # ):
    #     ticket = await self.get_ticket(ticket_id, session)
    #     user = await self.get_user(user_id, session)

    #     self.check_ticket_access(ticket, user, user_id)

    #     result = await session.execute(
    #         select(TicketHistory).where(TicketHistory.ticket_id == ticket_id).order_by(TicketHistory.changed_at.desc())
    #     )
    #     history_entries = result.scalars().all()
    #     return history_entries

    async def get_ticket_history(
        self,
        ticket_id: UUID,
        user_id: UUID,
        session: AsyncSession,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        changed_by: Optional[UUID] = None,
        page: int = 1,
):
        user = await self.get_user(user_id, session)

        page = max(page, 1)
        offset = (page - 1) * HISTORY_PAGE_SIZE

        base_query = (
            select(TicketHistory)
            .join(Ticket, Ticket.ticket_id == TicketHistory.ticket_id)
        )

        filters = []

        if not is_privileged(user):
            filters.append(Ticket.created_by == user_id)

        if ticket_id:
            filters.append(TicketHistory.ticket_id == ticket_id)

        if status:
            filters.append(Ticket.status == status)
        if priority:
            filters.append(Ticket.priority == priority)
        if changed_by:
            filters.append(TicketHistory.changed_by == changed_by)

        if filters:
            base_query = base_query.where(*filters)

        # Get paginated results
        history_query = (
            base_query
            .order_by(TicketHistory.changed_at.desc())
            .offset(offset)
            .limit(HISTORY_PAGE_SIZE)
        )

        # Build a separate query to count total matching records
        # This is needed for pagination metadata (total pages, etc.)
        # We use the same base_query (with filters) to ensure accurate count
        count_query = select(func.count()).select_from(base_query.subquery())

        histories = (await session.execute(history_query)).scalars().all()  # Execute the history query and fetch all matching TicketHistory records
        total_count = (await session.execute(count_query)).scalar_one() # Execute the count query to get the total number of matching records

        return {
            "histories": histories,
            "total": total_count,
            "page": page,
            "page_size": HISTORY_PAGE_SIZE
        }