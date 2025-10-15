from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.db.models import User, UserRole
from .schemas import UserCreateModel
from src.auth.utils import generate_hash_password, verify_password  


class UserService:

    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        return user
    

    async def user_exists(self, email: str, session: AsyncSession) -> bool:
        user = await self.get_user_by_email(email, session)
        return user is not None
    

    async def create_user(self, user_data: UserCreateModel, session: AsyncSession) -> User:

        # Exclude password_confirm before creating the model
        user_data_dict = user_data.model_dump(exclude={"password_confirm"})
        new_user = User(**user_data_dict)

        # Hash password before saving
        new_user.password_hash = generate_hash_password(user_data.password)
        new_user.role = UserRole.USER

        # Save to DB
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        return new_user
