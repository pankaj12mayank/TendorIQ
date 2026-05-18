"""Queue Monitoring Service"""

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
    QUEUE_OCR,
    QUEUE_PARSING,
    QUEUE_EMAIL,
    QUEUE_ANALYSIS,
    QUEUE_NOTIFICATIONS,
    DEAD_LETTER_QUEUE,
    FAILED_QUEUE,
)


logger = logging.getLogger(__name__)


class QueueMonitor:
    def __init__(self, pool: Optional[RedisPool] = None):
        self._pool = pool

    async def get_pool(self) -> RedisPool:
        if self._pool:
            return self._pool
        return await redis.create_pool(REDIS_POOL_MAIN)

    async def close(self) -> None:
        if self._pool:
            await self._pool.aclose()

    async def get_stats(self) -> dict:
        pool = await self.get_pool()

        stats = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'queues': {},
            'totals': {
                'pending': 0,
                'active': 0,
                'completed': 0,
                'failed': 0,
                'dead_letter': 0,
            },
            'health': 'healthy',
            'warnings': [],
        }

        for queue_name, queue_key in QueueConfig.QUEUES.items():
            pending = await pool.llen(queue_key)
            active_key = f'{queue_key}:active'
            active = 0

            active_items = await pool.lrange(active_key, 0, -1)
            active = len(active_items)

            processed_key = f'{queue_key}:processed'
            processed = 0
            processed_val = await pool.get(processed_key)
            if processed_val:
                processed = int(processed_val)

            failed_key = f'{queue_key}:failed'
            failed = 0
            failed_val = await pool.get(failed_key)
            if failed_val:
                failed = int(failed_val)

            stats['queues'][queue_name] = {
                'pending': pending,
                'active': active,
                'processed_today': processed,
                'failed_today': failed,
            }
            stats['totals']['pending'] += pending
            stats['totals']['active'] += active
            stats['totals']['completed'] += processed
            stats['totals']['failed'] += failed

        stats['totals']['dead_letter'] = await pool.llen(DEAD_LETTER_QUEUE)
        stats['totals']['failed'] += await pool.llen(FAILED_QUEUE)

        if stats['totals']['dead_letter'] > 100:
            stats['health'] = 'degraded'
            stats['warnings'].append(f'High dead letter count: {stats["totals"]["dead_letter"]}')

        if stats['totals']['active'] == 0 and stats['totals']['pending'] > 1000:
            stats['health'] = 'degraded'
            stats['warnings'].append('Queue is not being processed')

        for queue_name, queue_stats in stats['queues'].items():
            if queue_stats.get('failed_today', 0) > queue_stats.get('processed_today', 1) * 0.5:
                stats['health'] = 'degraded'
                stats['warnings'].append(f'{queue_name} has high failure rate')

        return stats

    async def get_queue_details(self, queue_name: str) -> dict:
        pool = await self.get_pool()

        queue_key = QueueConfig.QUEUES.get(queue_name)
        if not queue_key:
            return {'error': f'Unknown queue: {queue_name}'}

        pending = await pool.llen(queue_key)
        active_key = f'{queue_key}:active'
        active_items = await pool.lrange(active_key, 0, -1)

        details = {
            'queue_name': queue_name,
            'pending': pending,
            'active_jobs': [],
            'oldest_pending_seconds': None,
            'avg_wait_time_seconds': None,
        }

        if pending > 0:
            oldest = await pool.lindex(queue_key, -1)
            if oldest:
                job_data = json.loads(oldest)
                enqueued = datetime.fromisoformat(job_data['enqueued_at'])
                age = (datetime.now(timezone.utc) - enqueued).total_seconds()
                details['oldest_pending_seconds'] = int(age)

        for item in active_items[:10]:
            try:
                job = json.loads(item)
                details['active_jobs'].append({
                    'job_id': job.get('job_id'),
                    'function': job.get('function'),
                    'started_at': job.get('started_at'),
                })
            except:
                continue

        return details

    async def get_worker_status(self) -> dict:
        pool = await self.get_pool()

        worker_key = f'{QueueConfig.PREFIX}:worker:info'
        worker_info = await pool.get(worker_key)

        active_jobs_pattern = f'{QueueConfig.PREFIX}:job:active:*'
        active_jobs = []
        cursor = 0
        while True:
            cursor, keys = await pool.scan(cursor, match=active_jobs_pattern, count=100)
            for key in keys:
                job_id = key.decode().split(':')[-1] if isinstance(key, bytes) else key.split(':')[-1]
                active_jobs.append(job_id)
            if cursor == 0:
                break

        return {
            'workers': worker_info.decode().decode() if worker_info else '{"status": "unknown"}',
            'active_jobs_count': len(active_jobs),
            'active_job_ids': active_jobs[:20],
        }

    async def get_job_history(
        self,
        job_id: Optional[str] = None,
        queue: Optional[str] = None,
        hours: int = 24,
    ) -> list[dict]:
        pool = await self.get_pool()

        if job_id:
            status_key = f'{QueueConfig.PREFIX}:job_status:{job_id}'
            data = await pool.get(status_key)
            if data:
                return [json.loads(data)]
            return []

        history_pattern = f'{QueueConfig.PREFIX}:job_status:*'
        all_keys = []
        cursor = 0
        while True:
            cursor, keys = await pool.scan(cursor, match=history_pattern, count=100)
            all_keys.extend(keys)
            if cursor == 0:
                break

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        results = []

        for key in all_keys:
            data = await pool.get(key)
            if data:
                job = json.loads(data)
                updated_at = job.get('updated_at')
                if updated_at:
                    job_time = datetime.fromisoformat(updated_at)
                    if job_time >= cutoff:
                        if queue is None or job.get('queue') == queue:
                            results.append(job)

        results.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return results[:100]

    async def get_throughput_stats(self, hours: int = 24) -> dict:
        pool = await self.get_pool()

        stats = {
            'period_hours': hours,
            'queues': {},
            'totals': {
                'enqueued': 0,
                'processed': 0,
                'failed': 0,
                'dead_letter': 0,
            },
        }

        for queue_name, queue_key in QueueConfig.QUEUES.items():
            enqueued = 0
            processed = 0
            failed = 0

            enqueued_key = f'{queue_key}:enqueued'
            enqueued_val = await pool.get(enqueued_key)
            if enqueued_val:
                enqueued = int(enqueued_val)

            processed_key = f'{queue_key}:processed'
            processed_val = await pool.get(processed_key)
            if processed_val:
                processed = int(processed_val)

            failed_key = f'{queue_key}:failed'
            failed_val = await pool.get(failed_key)
            if failed_val:
                failed = int(failed_val)

            stats['queues'][queue_name] = {
                'enqueued': enqueued,
                'processed': processed,
                'failed': failed,
                'success_rate': round((processed / (processed + failed) * 100) if (processed + failed) > 0 else 100, 2),
            }

            stats['totals']['enqueued'] += enqueued
            stats['totals']['processed'] += processed
            stats['totals']['failed'] += failed

        stats['totals']['dead_letter'] = await pool.llen(DEAD_LETTER_QUEUE)
        stats['totals']['failed'] += stats['totals']['dead_letter']

        return stats

    async def get_slow_jobs(self, threshold_seconds: int = 300) -> list[dict]:
        pool = await self.get_pool()

        active_pattern = f'{QueueConfig.PREFIX}:job:active:*'
        slow_jobs = []
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold_seconds)

        cursor = 0
        while True:
            cursor, keys = await pool.scan(cursor, match=active_pattern, count=100)
            for key in keys:
                job_data = await pool.get(key)
                if job_data:
                    job = json.loads(job_data)
                    started_at = job.get('started_at')
                    if started_at:
                        start_time = datetime.fromisoformat(started_at)
                        if start_time < cutoff:
                            job['elapsed_seconds'] = int(
                                (datetime.now(timezone.utc) - start_time).total_seconds()
                            )
                            slow_jobs.append(job)
            if cursor == 0:
                break

        return sorted(slow_jobs, key=lambda x: x.get('elapsed_seconds', 0), reverse=True)[:50]


class AlertHandler:
    @staticmethod
    async def check_health() -> dict:
        pool = await redis.create_pool(REDIS_POOL_MAIN)

        alerts = []
        stats = await QueueMonitor(pool).get_stats()

        if stats['health'] == 'degraded':
            alerts.extend(stats['warnings'])

        for warning in alerts:
            logger.warning(f'Queue Alert: {warning}')

        await pool.aclose()

        return {
            'healthy': stats['health'] == 'healthy',
            'alerts': alerts,
            'stats': stats,
        }

    @staticmethod
    async def get_queue_alerts() -> list[dict]:
        pool = await redis.create_pool(REDIS_POOL_MAIN)
        monitor = QueueMonitor(pool)

        alerts = []
        stats = await monitor.get_stats()

        for queue_name, queue_stats in stats['queues'].items():
            pending = queue_stats.get('pending', 0)
            if pending > 500:
                alerts.append({
                    'severity': 'warning',
                    'queue': queue_name,
                    'message': f'{queue_name} has {pending} pending jobs',
                })
            if pending > 1000:
                alerts.append({
                    'severity': 'critical',
                    'queue': queue_name,
                    'message': f'{queue_name} queue is severely backlogged: {pending} pending',
                })

        dead_letter_count = stats['totals'].get('dead_letter', 0)
        if dead_letter_count > 50:
            alerts.append({
                'severity': 'warning',
                'queue': 'dead_letter',
                'message': f'{dead_letter_count} jobs in dead letter queue',
            })
        if dead_letter_count > 200:
            alerts.append({
                'severity': 'critical',
                'queue': 'dead_letter',
                'message': f'Critical: {dead_letter_count} jobs in dead letter queue - needs attention',
            })

        await pool.aclose()
        return alerts