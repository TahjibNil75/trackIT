from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models.user import User, UserRole
from sqlmodel import select, func
from fastapi import HTTPException


class UserManagementService:
    async def get_user_by_id(
            self,
            user_id : UUID,
            session : AsyncSession,
    ) -> User:
        statement = select(User).where(User.user_id == user_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User not found"
            )
        return user
    
    async def update_user_role(
            self,
            user_id: UUID,
            new_role: UserRole,
            session: AsyncSession,
    ) -> User:
        user = await self.get_user_by_id(user_id, session)

        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Cannot change role of an ADMIN user."
            )
        user.role = new_role
        await session.commit()
        await session.refresh(user)
        return user
    
    async def list_all_users(
            self,
            session: AsyncSession,
            page: int = 1,
            page_size: int = 10,
            role : UserRole | None = None,
            is_active : bool | None = None,
    ) -> dict:
        statement = select(User)
        count_statement = select(func.count()).select_from(User)

        # If role is provided, only select users with that role.
        # If is_active is provided, filter by active status (True or False).
        if role:
            statement = statement.where(User.role == role)
            count_statement = count_statement.where(User.role == role)
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
            count_statement = count_statement.where(User.is_active == is_active)

        total_result = (await session.execute(count_statement)).scalar_one()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = statement.offset(offset).limit(page_size).order_by(User.created_at.desc())

        users = (await session.execute(query)).scalars().all()

        return {
            "users": users,
            "total": total_result,
            "page": page,
            "page_size": page_size,
        }
    
    async def update_status(
            self,
            user_id: UUID,
            is_active: bool,
            session: AsyncSession,
    ) -> User:
        user = await self.get_user_by_id(user_id, session)

        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Cannot change status of an ADMIN user."
            )
        user.is_active = is_active
        await session.commit()
        await session.refresh(user)
        return user

    async def get_all_admins(
            self,
            session: AsyncSession,
            is_active: bool | None = None,
    ) -> list[User]:
        """Get all users with ADMIN role."""
        statement = select(User).where(User.role == UserRole.ADMIN)
        
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        
        statement = statement.order_by(User.created_at.desc())
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_all_support(
            self,
            session: AsyncSession,
            is_active: bool | None = None,
    ) -> list[User]:
        """Get all users with IT_SUPPORT role."""
        statement = select(User).where(User.role == UserRole.IT_SUPPORT)
        
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        
        statement = statement.order_by(User.created_at.desc())
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_all_managers(
            self,
            session: AsyncSession,
            is_active: bool | None = None,
    ) -> list[User]:
        """Get all users with MANAGER role."""
        statement = select(User).where(User.role == UserRole.MANAGER)
        
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        
        statement = statement.order_by(User.created_at.desc())
        result = await session.execute(statement)
        return list(result.scalars().all())

        

