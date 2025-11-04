from src.db.models.user import User
from src.db.models.ticket import Ticket
from src.db.models.comment import Comment
from src.db.models.comment import CommentVisibility
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime
from src.errors import (
    TicketNotFoundError,
    UserNotFoundError,
    UnauthorizedError,
    CommentNotFoundError,
)


INTERNAL_COMMENT_ROLES = {"admin", "it_support"}
PRIVILEGED_ROLES = {"admin", "manager", "it_support"}


def can_post_internal_comment(user: User) -> bool:
    """Check if the user has permission to post internal comments"""
    return user.role.value.lower() in INTERNAL_COMMENT_ROLES


def is_privileged(user: User) -> bool:
    return user.role.value.lower() in PRIVILEGED_ROLES


class CommentService:
    async def get_ticket(self, ticket_id: UUID, session: AsyncSession) -> Ticket:
        ticket = (await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )).scalar_one_or_none()
        if not ticket:
            raise TicketNotFoundError()
        return ticket

    async def get_user(self, user_id: UUID, session: AsyncSession) -> User:
        user = (await session.execute(
            select(User).where(User.user_id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise UserNotFoundError()
        return user

    async def get_comment(self, comment_id: UUID, session: AsyncSession) -> Comment:
        comment = (await session.execute(
            select(Comment).where(Comment.comment_id == comment_id)
        )).scalar_one_or_none()
        if not comment:
            raise CommentNotFoundError()
        return comment

    def can_comment(self, ticket: Ticket, user: User, visibility: CommentVisibility) -> bool:
        if visibility == CommentVisibility.INTERNAL:
            return can_post_internal_comment(user)
        return (
            is_privileged(user)
            or str(ticket.created_by) == str(user.user_id)
            or (ticket.assigned_to and str(ticket.assigned_to) == str(user.user_id))
        )

    async def create_comment(
        self,
        content: str,
        ticket_id: UUID,
        user_id: UUID,
        visibility: CommentVisibility,
        session: AsyncSession,
    ):
        ticket = await self.get_ticket(ticket_id, session)
        user = await self.get_user(user_id, session)

        if not self.can_comment(ticket, user, visibility):
            raise UnauthorizedError("You are not allowed to post comment on this ticket.")

        new_comment = Comment(
            content=content,
            ticket_id=ticket_id,
            user_id=user_id,
            visibilty=visibility,
        )
        session.add(new_comment)
        await session.commit()
        await session.refresh(new_comment)
        return new_comment

    async def update_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
        updated_comment: str,
        session: AsyncSession,
    ) -> Comment:
        comment = await self.get_comment(comment_id, session)
        if not comment:
            raise CommentNotFoundError()
        
        user = await self.get_user(user_id, session)
        if not user:
            raise UserNotFoundError()

        if user.role.value.lower() not in {"admin", "it_support", "manager"} and str(comment.user_id) != str(user.user_id):
            raise UnauthorizedError("Only the owner or privileged users can update this comment.")

        comment.content = updated_comment
        comment.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(comment)
        return comment

    async def delete_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ):
        comment = await self.get_comment(comment_id, session)
        if not comment:
            raise CommentNotFoundError()
        
        user = await self.get_user(user_id, session)
        if not user:
            raise UserNotFoundError()

        if user.role.value.lower() != "admin" and str(comment.user_id) != str(user.user_id):
            raise UnauthorizedError("Only the owner or an admin can delete this comment.")

        await session.delete(comment)
        await session.commit()
        return True
