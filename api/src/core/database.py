"""Database Configuration and Session Management"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

from .models import Base


def _engine_kwargs() -> dict:
    url = settings.DATABASE_URL
    if url.startswith('sqlite'):
        return {
            'echo': settings.DATABASE_ECHO,
            'connect_args': {'check_same_thread': False},
            'poolclass': StaticPool,
        }
    connect_args: dict = {}
    if settings.is_development and 'mysql' in url:
        connect_args['connect_timeout'] = 3
    return {
        'echo': settings.DATABASE_ECHO,
        'pool_size': settings.DATABASE_POOL_SIZE,
        'max_overflow': settings.DATABASE_MAX_OVERFLOW,
        'pool_pre_ping': settings.DATABASE_POOL_PRE_PING,
        'pool_recycle': settings.DATABASE_POOL_RECYCLE,
        'connect_args': connect_args,
    }


engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs())

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


async def _ensure_dev_accounts_on_startup() -> None:
    """Guarantee system owner + demo passwords whenever API starts in dev."""
    try:
        from .local_user_auth import ensure_dev_accounts

        async with async_session_maker() as session:
            if await ensure_dev_accounts(session):
                logger.info('Dev login accounts ensured (.tenderiq/owner-account.txt)')
    except Exception as exc:
        logger.warning('Dev account bootstrap skipped: %s', exc)


async def init_db() -> None:
    logger.info('Verifying database connection (%s)', settings.DATABASE_DRIVER)
    try:
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
            if settings.uses_sqlite:
                await conn.run_sync(Base.metadata.create_all)
                logger.info('SQLite schema ready (tables created if missing)')
            else:
                logger.info(
                    'Database connection verified (schema via alembic upgrade head)'
                )
        if settings.is_development:
            await _ensure_dev_accounts_on_startup()
    except Exception as exc:
        if _allow_start_without_db():
            logger.warning('Database unavailable (ALLOW_START_WITHOUT_DB=1): %s', exc)
            return
        hint = (
            'Set DATABASE_DRIVER=sqlite in .env for zero-install local dev, '
            'or fix MySQL and run alembic upgrade head'
        )
        raise RuntimeError(f'Database unavailable. {hint}') from exc


async def close_db() -> None:
    logger.info('Closing database connection')
    await engine.dispose()
    logger.info('Database connection closed')
