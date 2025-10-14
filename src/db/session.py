from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config import Config
import ssl

# Create async engine with SSL context (required by Neon)
engine: AsyncEngine = create_async_engine(
    url=Config.DATABASE_URL,
    echo=True,
    connect_args={"ssl": ssl.create_default_context()}  # Neon requires SSL
)

# Async session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
