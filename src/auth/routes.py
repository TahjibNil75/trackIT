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
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse
from src.errors import (
    NotFoundError,
    InvalidCredentialsError,
)
from .dependencies import get_current_user, RefreshTokenBearer



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
                "role": user.role.value,
            }
        }
    )


@auth_router.get(
    "/me",
    response_model=UserResponseModel,
    status_code=status.HTTP_200_OK,
)
async def get_current_user(
    user = Depends(get_current_user)
):
    return user


@auth_router.get("/refresh_token")
async def get_new_access_token(
    token_details: dict = Depends(RefreshTokenBearer())
):
    expiry_timestamp = token_details.get("exp")
    if datetime.fromtimestamp(expiry_timestamp) < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please login again.",
        )

    user_data = token_details.get("user")
    new_access_token = create_access_token(user_data=user_data)
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

