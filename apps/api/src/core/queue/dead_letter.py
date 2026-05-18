"""Dead Letter Queue Handler"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import redis.asyncio as redis
from arq.connections import RedisPool

from .config import (
    QueueConfig,
    DEAD_LETTER_QUEUE,
    FAILED_QUEUE,
    REDIS_POOL_MAIN,
)


logger = logging.getLogger(__name__)


class DeadLetterHandler:
    def __init__(self, pool: Optional[RedisPool] = None):
        self._pool = pool

    async def get_pool(self) -> RedisPool:
        if self._pool:
            return self._pool
        return await redis.create_pool(REDIS_POOL_MAIN)

    async def close(self) -> None:
        if self._pool:
            await self._pool.aclose()

    async def get_dead_letters(
        self,
        offset: int = 0,
        limit: int = 50,
        queue_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> list[dict]:
        pool = await self.get_pool()
        items = await pool.lrange(DEAD_LETTER_QUEUE, offset, offset + limit - 1)

        results = []
        for item in items:
            dl = json.loads(item)
            if queue_filter and dl.get('original_queue') != queue_filter:
                continue
            if date_from:
                failed_at = datetime.fromisoformat(dl['failed_at'])
                if failed_at < date_from:
                    continue
            if date_to:
                failed_at = datetime.fromisoformat(dl['failed_at'])
                if failed_at > date_to:
                    continue
            results.append(dl)

        return results

    async def retry_job(self, job_id: str) -> bool:
        pool = await self.get_pool()
        items = await pool.lrange(DEAD_LETTER_QUEUE, 0, -1)

        for item in items:
            dl = json.loads(item)
            if dl.get('job_id') == job_id:
                await pool.lrem(DEAD_LETTER_QUEUE, 1, item)

                retry_data = {
                    'function': dl['job_name'],
                    'args': dl.get('job_args', []),
                    'kwargs': {**dl.get('job_kwargs', {}), '_retry_from_dl': True},
                    'retry_count': dl.get('attempts', 0),
                    'original_error': dl.get('error'),
                    'retried_at': datetime.now(timezone.utc).isoformat(),
                }

                queue = dl.get('original_queue', QueueConfig.QUEUES['ocr'])
                retry_key = f'{queue}:retry'
                await pool.lpush(retry_key, json.dumps(retry_data))
                await pool.expire(retry_key, QueueConfig.JOB_TTL)

                logger.info(f'Requeued dead letter job {job_id} to {retry_key}')
                return True

        return False

    async def retry_all(self, queue_filter: Optional[str] = None) -> dict:
        pool = await self.get_pool()
        items = await pool.lrange(DEAD_LETTER_QUEUE, 0, -1)

        retried = 0
        failed = 0
        queues = {}

        for item in items:
            dl = json.loads(item)
            if queue_filter and dl.get('original_queue') != queue_filter:
                continue

            await pool.lrem(DEAD_LETTER_QUEUE, 1, item)

            retry_data = {
                'function': dl['job_name'],
                'args': dl.get('job_args', []),
                'kwargs': {**dl.get('job_kwargs', {}), '_retry_from_dl': True},
                'retry_count': dl.get('attempts', 0),
                'original_error': dl.get('error'),
                'retried_at': datetime.now(timezone.utc).isoformat(),
            }

            queue = dl.get('original_queue', QueueConfig.QUEUES['ocr'])
            retry_key = f'{queue}:retry'
            await pool.lpush(retry_key, json.dumps(retry_data))
            await pool.expire(retry_key, QueueConfig.JOB_TTL)

            if queue not in queues:
                queues[queue] = 0
            queues[queue] += 1
            retried += 1

        return {'retried': retried, 'failed': failed, 'queues': queues}

    async def discard_job(self, job_id: str) -> bool:
        pool = await self.get_pool()
        items = await pool.lrange(DEAD_LETTER_QUEUE, 0, -1)

        for item in items:
            dl = json.loads(item)
            if dl.get('job_id') == job_id:
                await pool.lrem(DEAD_LETTER_QUEUE, 1, item)
                logger.info(f'Discarded dead letter job {job_id}')
                return True

        return False

    async def discard_all(self, queue_filter: Optional[str] = None) -> int:
        pool = await self.get_pool()
        items = await pool.lrange(DEAD_LETTER_QUEUE, 0, -1)

        discarded = 0
        for item in items:
            dl = json.loads(item)
            if queue_filter and dl.get('original_queue') != queue_filter:
                continue
            await pool.lrem(DEAD_LETTER_QUEUE, 1, item)
            discarded += 1

        return discarded

    async def get_job_details(self, job_id: str) -> Optional[dict]:
        pool = await self.get_pool()
        items = await pool.lrange(DEAD_LETTER_QUEUE, 0, -1)

        for item in items:
            dl = json.loads(item)
            if dl.get('job_id') == job_id:
                return dl
        return None

    async def move_to_failed(self, job_id: str) -> bool:
        dl = await self.get_job_details(job_id)
        if not dl:
            return False

        pool = await self.get_pool()
        await self.discard_job(job_id)

        failed_data = {
            'job_id': job_id,
            'job_name': dl.get('job_name'),
            'error': dl.get('error'),
            'attempts': dl.get('attempts', 0),
            'max_retries': dl.get('max_retries', 3),
            'original_queue': dl.get('original_queue'),
            'moved_to_failed_at': datetime.now(timezone.utc).isoformat(),
            'args': dl.get('job_args', []),
            'kwargs': dl.get('job_kwargs', {}),
        }
        await pool.lpush(FAILED_QUEUE, json.dumps(failed_data))
        await pool.expire(FAILED_QUEUE, QueueConfig.JOB_TTL)

        return True


class FailedJobsHandler:
    def __init__(self, pool: Optional[RedisPool] = None):
        self._pool = pool

    async def get_pool(self) -> RedisPool:
        if self._pool:
            return self._pool
        return await redis.create_pool(REDIS_POOL_MAIN)

    async def close(self) -> None:
        if self._pool:
            await self._pool.aclose()

    async def get_failed_jobs(
        self,
        offset: int = 0,
        limit: int = 50,
        job_name_filter: Optional[str] = None,
    ) -> list[dict]:
        pool = await self.get_pool()
        items = await pool.lrange(FAILED_QUEUE, offset, offset + limit - 1)

        results = []
        for item in items:
            fj = json.loads(item)
            if job_name_filter and fj.get('job_name') != job_name_filter:
                continue
            results.append(fj)

        return results

    async def retry_failed_job(self, job_id: str) -> bool:
        pool = await self.get_pool()
        items = await pool.lrange(FAILED_QUEUE, 0, -1)

        for item in items:
            fj = json.loads(item)
            if fj.get('job_id') == job_id:
                await pool.lrem(FAILED_QUEUE, 1, item)

                retry_data = {
                    'function': fj['job_name'],
                    'args': fj.get('args', []),
                    'kwargs': {**fj.get('kwargs', {}), '_retry_from_failed': True},
                    'retry_count': fj.get('attempts', 0),
                    'original_error': fj.get('error'),
                    'retried_at': datetime.now(timezone.utc).isoformat(),
                }

                queue = fj.get('original_queue', QueueConfig.QUEUES['ocr'])
                await pool.lpush(queue, json.dumps(retry_data))
                await pool.expire(queue, QueueConfig.JOB_TTL)

                logger.info(f'Retried failed job {job_id} from failed queue')
                return True

        return False

    async def clear_failed_jobs(self, older_than_days: int = 30) -> int:
        pool = await self.get_pool()
        items = await pool.lrange(FAILED_QUEUE, 0, -1)

        cleared = 0
        cutoff = datetime.now(timezone.utc).timestamp() - (older_than_days * 86400)

        for item in items:
            fj = json.loads(item)
            failed_at = datetime.fromisoformat(fj['failed_at']).timestamp()
            if failed_at < cutoff:
                await pool.lrem(FAILED_QUEUE, 1, item)
                cleared += 1

        return cleared

    async def get_failed_stats(self) -> dict:
        pool = await self.get_pool()
        total = await pool.llen(FAILED_QUEUE)

        by_job = {}
        items = await pool.lrange(FAILED_QUEUE, 0, -1)
        for item in items:
            fj = json.loads(item)
            job_name = fj.get('job_name', 'unknown')
            if job_name not in by_job:
                by_job[job_name] = 0
            by_job[job_name] += 1

        return {
            'total': total,
            'by_job': by_job,
        }