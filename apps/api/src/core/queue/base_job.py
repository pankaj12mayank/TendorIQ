"""Base Job Definition with retry strategy"""

import json
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from arq import cron
from arq.connections import RedisPool
from arq.jobs import JobStatus

from .config import (
    QueueConfig,
    DEAD_LETTER_QUEUE,
    FAILED_QUEUE,
    REDIS_POOL_MAIN,
)


class JobPriority(int, Enum):
    HIGH = 10
    NORMAL = 5
    LOW = 1


class JobState(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    RETRY = 'retry'
    DEAD = 'dead'
    CANCELLED = 'cancelled'


class BaseJob(ABC):
    queue_name: str = QueueConfig.PREFIX
    job_name: str = 'base'
    job_timeout: int = QueueConfig.DEFAULT_TIMEOUT
    max_retries: int = QueueConfig.MAX_RETRIES

    def __init__(
        self,
        ctx: dict,
        job_id: Optional[str] = None,
        document_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        priority: int = JobPriority.NORMAL,
        metadata: Optional[dict] = None,
    ):
        self.ctx = ctx
        self.job_id = job_id
        self.document_id = document_id
        self.tenant_id = tenant_id
        self.priority = priority
        self.metadata = metadata or {}
        self._started_at: Optional[datetime] = None
        self._ended_at: Optional[datetime] = None
        self._error: Optional[str] = None
        self._attempts: int = 0

    @abstractmethod
    async def run(self, *args, **kwargs) -> dict:
        pass

    async def update_status(
        self,
        status: JobState,
        error: Optional[str] = None,
        result: Optional[dict] = None,
    ) -> None:
        if status == JobState.RUNNING and not self._started_at:
            self._started_at = datetime.now(timezone.utc)
        elif status in (JobState.SUCCESS, JobState.FAILED, JobState.DEAD):
            self._ended_at = datetime.now(timezone.utc)

        if error:
            self._error = error

        pool: RedisPool = self.ctx.get('redis_pool')
        if pool:
            key = f'{QueueConfig.PREFIX}:job_status:{self.job_id}'
            data = {
                'job_id': self.job_id,
                'job_name': self.job_name,
                'status': status.value,
                'document_id': str(self.document_id) if self.document_id else None,
                'tenant_id': str(self.tenant_id) if self.tenant_id else None,
                'attempts': self._attempts,
                'max_retries': self.max_retries,
                'error': self._error,
                'result': result,
                'started_at': self._started_at.isoformat() if self._started_at else None,
                'ended_at': self._ended_at.isoformat() if self._ended_at else None,
                'metadata': self.metadata,
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            await pool.set(key, json.dumps(data), ex=QueueConfig.JOB_TTL)

    async def on_start(self) -> None:
        self._attempts += 1
        await self.update_status(JobState.RUNNING)

    async def on_success(self, result: dict) -> None:
        await self.update_status(JobState.SUCCESS, result=result)

    async def on_failure(self, error: Exception) -> None:
        tb = traceback.format_exc()
        self._error = f'{str(error)}\n{tb}'
        await self.update_status(JobState.FAILED, error=self._error)


class RetryHandler:
    @staticmethod
    def get_retry_delay(attempts: int) -> int:
        delays = QueueConfig.RETRY_DELAYS
        idx = min(attempts - 1, len(delays) - 1)
        return delays[idx] if idx >= 0 else delays[-1]

    @staticmethod
    async def move_to_dead_letter(
        pool: RedisPool,
        job_id: str,
        job_data: dict,
        error: str,
    ) -> None:
        dl_data = {
            'job_id': job_id,
            'original_queue': job_data.get('queue', 'unknown'),
            'job_name': job_data.get('function', 'unknown'),
            'error': error,
            'attempts': job_data.get('attempts', 0),
            'max_retries': job_data.get('max_retries', 3),
            'failed_at': datetime.now(timezone.utc).isoformat(),
            'job_args': job_data.get('args', []),
            'job_kwargs': job_data.get('kwargs', {}),
            'metadata': job_data.get('metadata', {}),
        }
        await pool.lpush(DEAD_LETTER_QUEUE, json.dumps(dl_data))
        await pool.expire(DEAD_LETTER_QUEUE, QueueConfig.JOB_TTL)

    @staticmethod
    async def log_failed_job(
        pool: RedisPool,
        job_id: str,
        job_data: dict,
        error: str,
    ) -> None:
        failed_data = {
            'job_id': job_id,
            'job_name': job_data.get('function', 'unknown'),
            'error': error,
            'attempts': job_data.get('attempts', 0),
            'failed_at': datetime.now(timezone.utc).isoformat(),
            'args': job_data.get('args', []),
            'kwargs': job_data.get('kwargs', {}),
        }
        await pool.lpush(FAILED_QUEUE, json.dumps(failed_data))
        await pool.expire(FAILED_QUEUE, QueueConfig.JOB_TTL)


class JobTracker:
    @staticmethod
    async def get_job_status(pool: RedisPool, job_id: str) -> Optional[dict]:
        key = f'{QueueConfig.PREFIX}:job_status:{job_id}'
        data = await pool.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    async def get_active_jobs(pool: RedisPool) -> list[dict]:
        pattern = f'{QueueConfig.PREFIX}:job_status:*'
        keys = []
        cursor = 0
        while True:
            cursor, batch = await pool.scan(cursor, match=pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break

        jobs = []
        for key in keys:
            data = await pool.get(key)
            if data:
                jobs.append(json.loads(data))
        return jobs

    @staticmethod
    async def get_queue_stats(pool: RedisPool) -> dict:
        stats = {
            'queues': {},
            'total_pending': 0,
            'total_active': 0,
            'dead_letter_count': 0,
            'failed_count': 0,
        }

        for queue_name in QueueConfig.QUEUES.values():
            pending = await pool.llen(queue_name)
            active_key = f'{queue_name}:active'
            active = await pool.llen(active_key) if await pool.exists(active_key) else 0
            stats['queues'][queue_name] = {
                'pending': pending,
                'active': active,
            }
            stats['total_pending'] += pending

        stats['dead_letter_count'] = await pool.llen(DEAD_LETTER_QUEUE)
        stats['failed_count'] = await pool.llen(FAILED_QUEUE)
        return stats

    @staticmethod
    async def retry_dead_letter(pool: RedisPool, job_id: str) -> bool:
        cursor = 0
        while True:
            cursor, items = await pool.scan(cursor, match=f'{DEAD_LETTER_QUEUE}', count=100)
            for item in items:
                data = await pool.lrange(item, 0, -1)
                for raw in data:
                    dl = json.loads(raw)
                    if dl.get('job_id') == job_id:
                        await pool.lrem(item, 1, raw)
                        new_job_data = {
                            'function': dl['job_name'],
                            'args': dl.get('job_args', []),
                            'kwargs': {**dl.get('job_kwargs', {}), '_retry': True},
                        }
                        queue = dl.get('original_queue', QueueConfig.QUEUES['ocr'])
                        await pool.lpush(queue, json.dumps(new_job_data))
                        return True
            if cursor == 0:
                break
        return False
