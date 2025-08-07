import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./campusflow.db",
)

# Async engine for production use
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Sync engine for Alembic migrations
if DATABASE_URL.startswith("sqlite"):
    sync_database_url = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite:///")
else:
    sync_database_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
sync_engine = create_engine(sync_database_url, echo=True)

# Session makers
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    with SessionLocal() as session:
        try:
            yield session
        finally:
            session.close()


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
