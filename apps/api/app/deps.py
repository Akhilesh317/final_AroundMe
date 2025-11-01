"""FastAPI dependencies"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_redis_client
from app.db.session import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis():
    """Get Redis client"""
    return await get_redis_client()