from fastapi import APIRouter
from .schemas import UserResponseModel, UserCreateModel
from fastapi import Depends, HTTPException, status
from .service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.errors import (
    UserAlreadyExistsError,
)




auth_router = APIRouter()
user_service = UserService()



@auth_router.post(
    "/signup",
    response_model=UserResponseModel,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    user_data: UserCreateModel,
    session: AsyncSession = Depends (get_session),
):
    email = user_data.email
    user_exists = await user_service.user_exists(email, session)
    if user_exists:
        raise UserAlreadyExistsError(email)
    new_user = await user_service.create_user(user_data, session)
    return new_user
