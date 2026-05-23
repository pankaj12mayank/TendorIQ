"""Database Configuration and Session Management"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

from .models import Base


_connect_args: dict = {}
if settings.is_development and 'mysql' in settings.DATABASE_URL:
    _connect_args['connect_timeout'] = 3

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    connect_args=_connect_args,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """Create and return a standalone session (caller must close it)."""
    return async_session_maker()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _allow_start_without_db() -> bool:
    return os.getenv('ALLOW_START_WITHOUT_DB', '').lower() in ('1', 'true', 'yes')


async def init_db() -> None:
    logger.info('Verifying database connection')
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        logger.info(
            'Database connection verified (schema via Alembic: cd apps/api && alembic upgrade head)'
        )
    except Exception as exc:
        if _allow_start_without_db():
            logger.warning('Database unavailable (ALLOW_START_WITHOUT_DB=1): %s', exc)
            return
        raise RuntimeError(
            'Database unavailable. Start MySQL, set DATABASE_URL in .env, '
            'and run: alembic upgrade head'
        ) from exc


async def close_db() -> None:
    logger.info('Closing database connection')
    await engine.dispose()
    logger.info('Database connection closed')
