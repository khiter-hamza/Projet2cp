from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=True,  # Set to False in production
    pool_pre_ping=True,
)

# Create sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    # Register all models here for Base.metadata.create_all
    from app.models.user import User
    from app.models.laboratory import Laboratory
    from app.models.application import Application
    
    # This is typically handled by Alembic, but good for simple startup tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
