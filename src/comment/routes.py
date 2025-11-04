from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from .service import CommentService
from src.auth.dependencies import AccessTokenBearer, role_checker
from .schemas import CommentResponse, CommentCreateRequest, CommentUpdateRequest
from src.db.main import get_session

comment_router = APIRouter()
comment_service = CommentService()
AllUsers = Depends(role_checker(["user", "manager", "it_support", "admin"]))


@comment_router.post(
    "/create/{ticket_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentResponse,
    dependencies=[AllUsers],
)
async def create_comment(
    comment_data: CommentCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]

    return await comment_service.create_comment(
        content=comment_data.content,
        ticket_id=comment_data.ticket_id,
        user_id=user_id,
        visibility=comment_data.visibility,
        session=session,
    )


@comment_router.put(
    "/update/{comment_id}",
    response_model=CommentResponse,
    dependencies=[AllUsers],
    status_code=status.HTTP_200_OK,
)
async def update_comment(
    comment_id: UUID,
    update_comment: CommentUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]

    return await comment_service.update_comment(
        comment_id=comment_id,
        updated_comment=update_comment.content,
        user_id=user_id,
        session=session,
    )


@comment_router.delete(
    "/delete/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AllUsers],
)
async def delete_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]

    await comment_service.delete_comment(comment_id, user_id, session)
    return {"detail": "Comment deleted successfully"}
