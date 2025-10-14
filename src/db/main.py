from sqlalchemy import text
from src.db.session import engine
from sqlmodel import SQLModel
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker 


# Initialize database and create tables
async def init_db():
    from .models import User  # import models here to ensure they are registered
    async with engine.begin() as conn:
        # Create all tables based on the models
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Database connection established and tables created successfully!")


# Provide an async DB session generator
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(engine, expire_on_commit=False)  
    async with async_session() as session:
        yield session





###########################################################################
##      During Project Setup It required when no models are present 
###########################################################################
# async def init_db() -> None:
#     """
#     Initialize the database connection.
#     For now:
#       - Just test the connection with a simple query.
#     Later:
#       - Will create tables automatically when models are added.
#     """
#     async with engine.begin() as conn:
#         await conn.execute(text("SELECT 1"))
#         print("✅ Database connection established successfully!")

 ###-----------------------------------------------------------------------------------------------###
  ###-----------------------------------------------------------------------------------------------###
   ###-----------------------------------------------------------------------------------------------###

# async def reset_db():
#     from .models import User
#     async with engine.begin() as conn:
#         # Drop all tables based on the models
#         await conn.run_sync(SQLModel.metadata.drop_all)
#         print("🗑️  All tables dropped successfully!")
#         # Create all tables based on the models
#         await conn.run_sync(SQLModel.metadata.create_all)
#         print("Database connection established and tables created successfully!")


# async def drop_db():
#     from .models import User
#     async with engine.begin() as conn:
#         # Drop all tables based on the models
#         await conn.run_sync(SQLModel.metadata.drop_all)
#         print("All tables dropped successfully!")