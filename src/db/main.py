from sqlalchemy import text
from src.db.session import engine


async def init_db() -> None:
    """
    Initialize the database connection.
    For now:
      - Just test the connection with a simple query.
    Later:
      - Will create tables automatically when models are added.
    """
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
        print("✅ Database connection established successfully!")
