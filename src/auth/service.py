from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models import User
from sqlmodel import select
from .schemas import UserCreateModel


class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        user = result.first()
        return user
    
    async def user_exists(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        return True if user is not None else False
    
    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        user_data_dict = user_data.model_dump(exclude={"password_confirm"})
        new_user = User(**user_data_dict)
        new_user.password_hash = user_data.password
        new_user.role = "user"
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
    

