from sqlalchemy import text
from src.db.session import engine
from sqlmodel import SQLModel


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

async def init_db():
    from .models import User
    async with engine.begin() as conn:
        # Create all tables based on the models
        await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Database connection established and tables created successfully!")
