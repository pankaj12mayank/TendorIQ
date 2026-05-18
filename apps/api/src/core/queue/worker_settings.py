"""ARQ Worker Settings"""

import logging
from typing import Optional

from arq.connections import RedisPool
from arq.constants import (
    DefaultQueueName,
    HealthCheckKey,
    WorkerKey,
)

from .config import (
    QueueConfig,
    REDIS_POOL_MAIN,
    QUEUE_OCR,
    QUEUE_PARSING,
    QUEUE_EMAIL,
    QUEUE_ANALYSIS,
    QUEUE_NOTIFICATIONS,
    DEAD_LETTER_QUEUE,
    FAILED_QUEUE,
)
from .jobs import JOB_FUNCTIONS


logger = logging.getLogger(__name__)


class WorkerSettings:
    redis_pool = REDIS_POOL_MAIN

    functions = [
        JOB_FUNCTIONS['ocr_process'],
        JOB_FUNCTIONS['ocr_batch'],
        JOB_FUNCTIONS['parsing_process'],
        JOB_FUNCTIONS['parsing_batch'],
        JOB_FUNCTIONS['chunking_process'],
        JOB_FUNCTIONS['document_analysis'],
        JOB_FUNCTIONS['batch_analysis'],
        JOB_FUNCTIONS['email_send'],
        JOB_FUNCTIONS['notification_send'],
        JOB_FUNCTIONS['webhook_call'],
        JOB_FUNCTIONS['scheduled_report'],
    ]

    queue_settings = {
        QUEUE_OCR: {
            'timeout': 600,
            'max_tries': 3,
            'min_retry_delay': 30,
            'max_retry_delay': 600,
        },
        QUEUE_PARSING: {
            'timeout': 900,
            'max_tries': 3,
            'min_retry_delay': 30,
            'max_retry_delay': 600,
        },
        QUEUE_EMAIL: {
            'timeout': 120,
            'max_tries': 3,
            'min_retry_delay': 30,
            'max_retry_delay': 600,
        },
        QUEUE_ANALYSIS: {
            'timeout': 600,
            'max_tries': 3,
            'min_retry_delay': 30,
            'max_retry_delay': 600,
        },
        QUEUE_NOTIFICATIONS: {
            'timeout': 60,
            'max_tries': 3,
            'min_retry_delay': 30,
            'max_retry_delay': 600,
        },
    }

    max_jobs = 10
    job_timeout = 300
    keep_result = 86400
    keep_failed = 259200
    allow_abort = True
    max_retries = 3

    health_check_interval = 30
    max_concurrent_tasks = 10

    after_job_end = None

    async def on_worker_start(self, ctx: dict) -> None:
        logger.info('Worker started')
        pool: RedisPool = ctx['redis']
        await pool.set(
            f'{QueueConfig.PREFIX}:worker:info',
            '{"status": "running", "started_at": ""}',
            ex=3600,
        )

    async def on_worker_shutdown(self, ctx: dict) -> None:
        logger.info('Worker shutting down')
        pool: RedisPool = ctx['redis']
        await pool.set(
            f'{QueueConfig.PREFIX}:worker:info',
            '{"status": "shutdown", "stopped_at": ""}',
            ex=3600,
        )

    async def on_job_start(self, ctx: dict, job_id: str) -> None:
        logger.info(f'Job {job_id} started')

    async def on_job_end(self, ctx: dict, job_id: str, result: Optional[dict], exception: Optional[Exception]) -> None:
        if exception:
            logger.error(f'Job {job_id} failed: {exception}')
        else:
            logger.info(f'Job {job_id} completed')

    async def on_job_retry(self, ctx: dict, job_id: str, exception: Exception) -> None:
        logger.warning(f'Job {job_id} retry scheduled: {exception}')

    async def before_job_execute(self, ctx: dict, job_id: str) -> None:
        pool: RedisPool = ctx['redis']
        await pool.set(
            f'{QueueConfig.PREFIX}:job:active:{job_id}',
            '{"started_at": ""}',
            ex=self.job_timeout + 60,
        )

    async def after_job_execute(self, ctx: dict, job_id: str) -> None:
        pool: RedisPool = ctx['redis']
        await pool.delete(f'{QueueConfig.PREFIX}:job:active:{job_id}')