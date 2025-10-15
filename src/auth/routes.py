from fastapi import APIRouter
from .schemas import (
    UserCreateModel,
    UserResponseModel,
    UserLoginModel,
)
from fastapi import Depends, HTTPException, status
from .service import UserService
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.errors import (
    UserAlreadyExistsError,
)
from .utils import create_access_token, verify_password
from datetime import timedelta
from fastapi.responses import JSONResponse
from src.errors import (
    NotFoundError,
    InvalidCredentialsError,
)



auth_router = APIRouter()
user_service = UserService()

REFRESH_TOKEN_EXPIRY = 2



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



@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
)
async def login(
    login_data: UserLoginModel,
    session: AsyncSession = Depends(get_session)
):
    email = login_data.email
    password = login_data.password

    # 1️⃣ Check if user exists
    user = await user_service.get_user_by_email(email, session)
    if user is None:
        raise NotFoundError(email)

    # 2️⃣ Verify password
    password_valid = verify_password(password, user.password_hash)
    if not password_valid:
        raise InvalidCredentialsError()

    # 3️⃣ Create tokens
    access_token = create_access_token(
        user_data={
            "email": user.email,
            "user_id": str(user.user_id),
            "role": user.role.value, # Fix: ✅ convert enum to string
        }
    )

    refresh_token = create_access_token(
        user_data={
            "email": user.email,
            "user_id": str(user.user_id),
        },
        refresh=True,
        expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
    )

    # 4️⃣ Return response
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "user_id": str(user.user_id),
            }
        }
    )