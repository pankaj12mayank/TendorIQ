"""Redis Connection and Queue Management"""

import logging
from typing import Any

import redis.asyncio as redis
from arq import create_pool
from arq.typing import WorkerSettings

from .config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None
_arq_pool: Any = None


async def init_redis() -> None:
    global _redis_client, _arq_pool

    logger.info(f'Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}')

    _redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        socket_connect_timeout=5,
        socket_timeout=5,
    )

    await _redis_client.ping()
    logger.info('Redis connection established')

    _arq_pool = await create_pool(
        settings.redis_url,
        worker_settings=WorkerSettings(
            functions=[],
            burst=False,
            max_jobs=10,
            timeout=300,
        ),
    )
    logger.info('ARQ pool initialized')


async def close_redis() -> None:
    global _redis_client, _arq_pool

    if _arq_pool:
        await _arq_pool.close()
        logger.info('ARQ pool closed')

    if _redis_client:
        await _redis_client.close()
        logger.info('Redis connection closed')

    _redis_client = None
    _arq_pool = None


def get_redis() -> redis.Redis:
    if not _redis_client:
        raise RuntimeError('Redis not initialized. Call init_redis() first.')
    return _redis_client


def get_arq_pool() -> Any:
    if not _arq_pool:
        raise RuntimeError('ARQ pool not initialized. Call init_redis() first.')
    return _arq_pool


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    client = get_redis()
    await client.setex(key, ttl, str(value))


async def cache_get(key: str) -> str | None:
    client = get_redis()
    return await client.get(key)


async def cache_delete(key: str) -> None:
    client = get_redis()
    await client.delete(key)


async def cache_invalidate_pattern(pattern: str) -> None:
    client = get_redis()
    keys = await client.keys(pattern)
    if keys:
        await client.delete(*keys)