"""Failure Recovery System"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import redis.asyncio as redis
from arq.connections import RedisPool

from .config import (
    QueueConfig,
    REDIS_POOL_MAIN,
    DEAD_LETTER_QUEUE,
    FAILED_QUEUE,
    QUEUE_OCR,
    QUEUE_PARSING,
)
from .dead_letter import DeadLetterHandler, FailedJobsHandler


logger = logging.getLogger(__name__)


class FailureRecovery:
    def __init__(self, pool: Optional[RedisPool] = None):
        self._pool = pool
        self._dl_handler = DeadLetterHandler(pool)
        self._fj_handler = FailedJobsHandler(pool)

    async def get_pool(self) -> RedisPool:
        if self._pool:
            return self._pool
        return await redis.create_pool(REDIS_POOL_MAIN)

    async def close(self) -> None:
        if self._pool:
            await self._pool.aclose()

    async def recover_stuck_jobs(self, timeout_seconds: int = 3600) -> dict:
        pool = await self.get_pool()

        stuck_pattern = f'{QueueConfig.PREFIX}:job:active:*'
        recovered = []
        failed = []

        cursor = 0
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

        while True:
            cursor, keys = await pool.scan(cursor, match=stuck_pattern, count=100)
            for key in keys:
                job_data = await pool.get(key)
                if job_data:
                    job = json.loads(job_data)
                    started_at = job.get('started_at')
                    if started_at:
                        start_time = datetime.fromisoformat(started_at)
                        if start_time < cutoff:
                            job_id = key.decode().split(':')[-1] if isinstance(key, bytes) else key.split(':')[-1]

                            status_key = f'{QueueConfig.PREFIX}:job_status:{job_id}'
                            await pool.delete(key)

                            status_data = await pool.get(status_key)
                            if status_data:
                                status = json.loads(status_data)
                                status['status'] = 'retry'
                                status['recovery_note'] = 'Stuck job recovered'
                                await pool.set(status_key, json.dumps(status), ex=QueueConfig.JOB_TTL)

                            recovered.append(job_id)
                        else:
                            failed.append(job_id)

            if cursor == 0:
                break

        return {
            'recovered_count': len(recovered),
            'still_stuck': len(failed),
            'recovered_job_ids': recovered,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    async def recover_by_error_type(self, error_substring: str, target_queue: Optional[str] = None) -> dict:
        pool = await self.get_pool()

        dl_items = await pool.lrange(DEAD_LETTER_QUEUE, 0, -1)
        fj_items = await pool.lrange(FAILED_QUEUE, 0, -1)

        recovered = []
        for items, queue_name in [(dl_items, 'dead_letter'), (fj_items, 'failed')]:
            if target_queue and target_queue != queue_name:
                continue

            for item in items:
                data = json.loads(item)
                error = data.get('error', '')
                if error_substring.lower() in error.lower():
                    job_id = data.get('job_id')

                    if queue_name == 'dead_letter':
                        await self._dl_handler.retry_job(job_id)
                    else:
                        await self._fj_handler.retry_failed_job(job_id)

                    recovered.append({
                        'job_id': job_id,
                        'original_queue': data.get('original_queue', 'unknown'),
                        'error': error[:200],
                    })

        return {
            'recovered_count': len(recovered),
            'jobs': recovered,
            'error_filter': error_substring,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    async def bulk_recover_dead_letters(
        self,
        older_than_hours: int = 24,
        max_recover: int = 100,
        queue_filter: Optional[str] = None,
    ) -> dict:
        pool = await self.get_pool()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)

        items = await pool.lrange(DEAD_LETTER_QUEUE, 0, -1)

        recovered = []
        skipped = 0

        for item in items[:max_recover]:
            dl = json.loads(item)
            job_id = dl.get('job_id')
            failed_at = datetime.fromisoformat(dl['failed_at'])

            if failed_at < cutoff:
                if queue_filter and dl.get('original_queue') != queue_filter:
                    skipped += 1
                    continue

                success = await self._dl_handler.retry_job(job_id)
                if success:
                    recovered.append(job_id)

        return {
            'recovered_count': len(recovered),
            'skipped': skipped,
            'older_than_hours': older_than_hours,
            'max_recover': max_recover,
            'recovered_job_ids': recovered,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    async def reset_queue_stats(self, queue: Optional[str] = None) -> dict:
        pool = await self.get_pool()

        queues = [queue] if queue else list(QueueConfig.QUEUES.values())
        reset_queues = {}

        for q in queues:
            for suffix in ['enqueued', 'processed', 'failed', 'active']:
                key = f'{q}:{suffix}'
                await pool.delete(key)
            reset_queues[q] = True

        return {
            'reset_queues': list(reset_queues.keys()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    async def get_recovery_history(self, limit: int = 50) -> list[dict]:
        pool = await self.get_pool()

        history_key = f'{QueueConfig.PREFIX}:recovery:history'
        items = await pool.lrange(history_key, 0, limit - 1)

        return [json.loads(item) for item in items]

    async def log_recovery_action(self, action: str, details: dict) -> None:
        pool = await self.get_pool()

        history_key = f'{QueueConfig.PREFIX}:recovery:history'
        entry = {
            'action': action,
            'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        await pool.lpush(history_key, json.dumps(entry))
        await pool.expire(history_key, 604800)


class AutomaticRecovery:
    def __init__(self):
        self._recovery = FailureRecovery()

    async def run_scheduled_recovery(self) -> dict:
        results = {
            'stuck_jobs': None,
            'dead_letter_retries': None,
            'failed_cleanup': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        try:
            results['stuck_jobs'] = await self._recovery.recover_stuck_jobs(timeout_seconds=3600)
            logger.info(f"Recovered stuck jobs: {results['stuck_jobs']}")
        except Exception as e:
            logger.error(f"Failed to recover stuck jobs: {e}")
            results['stuck_jobs'] = {'error': str(e)}

        try:
            results['dead_letter_retries'] = await self._recovery.bulk_recover_dead_letters(
                older_than_hours=24,
                max_recover=50,
            )
            logger.info(f"Dead letter recovery: {results['dead_letter_retries']}")
        except Exception as e:
            logger.error(f"Failed to recover dead letters: {e}")
            results['dead_letter_retries'] = {'error': str(e)}

        try:
            pool = await self._recovery.get_pool()
            fj_handler = FailedJobsHandler(pool)
            cleared = await fj_handler.clear_failed_jobs(older_than_days=30)
            results['failed_cleanup'] = {'cleared': cleared}
            logger.info(f"Cleared {cleared} old failed jobs")
        except Exception as e:
            logger.error(f"Failed to cleanup failed jobs: {e}")
            results['failed_cleanup'] = {'error': str(e)}

        return results

    async def get_system_health(self) -> dict:
        pool = await self._recovery.get_pool()

        health = {
            'status': 'healthy',
            'checks': {},
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        try:
            await pool.ping()
            health['checks']['redis'] = 'ok'
        except Exception as e:
            health['checks']['redis'] = f'error: {e}'
            health['status'] = 'unhealthy'

        dl_count = await pool.llen(DEAD_LETTER_QUEUE)
        health['checks']['dead_letter_count'] = dl_count
        if dl_count > 100:
            health['status'] = 'degraded'

        failed_count = await pool.llen(FAILED_QUEUE)
        health['checks']['failed_count'] = failed_count

        stuck_pattern = f'{QueueConfig.PREFIX}:job:active:*'
        stuck_count = 0
        cursor = 0
        while True:
            cursor, keys = await pool.scan(cursor, match=stuck_pattern, count=100)
            stuck_count += len(keys)
            if cursor == 0:
                break
        health['checks']['stuck_jobs'] = stuck_count

        if stuck_count > 10:
            health['status'] = 'degraded'

        return health


class MaintenanceScheduler:
    @staticmethod
    async def run_hourly_maintenance() -> dict:
        recovery = FailureRecovery()
        results = {
            'hourly_cleanup': None,
            'queue_stats_reset': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        try:
            results['hourly_cleanup'] = await recovery.recover_stuck_jobs(timeout_seconds=7200)
        except Exception as e:
            results['hourly_cleanup'] = {'error': str(e)}

        return results

    @staticmethod
    async def run_daily_maintenance() -> dict:
        recovery = AutomaticRecovery()
        auto_rec = FailureRecovery()
        results = {
            'scheduled_recovery': None,
            'dead_letter_recovery': None,
            'failed_cleanup': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        try:
            results['scheduled_recovery'] = await recovery.run_scheduled_recovery()
        except Exception as e:
            results['scheduled_recovery'] = {'error': str(e)}

        try:
            pool = await auto_rec.get_pool()
            fj_handler = FailedJobsHandler(pool)
            cleared = await fj_handler.clear_failed_jobs(older_than_days=30)
            results['failed_cleanup'] = {'cleared': cleared}
        except Exception as e:
            results['failed_cleanup'] = {'error': str(e)}

        return results