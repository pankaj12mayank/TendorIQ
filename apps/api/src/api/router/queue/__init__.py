"""Queue Management API Router"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, EmailStr

from ...core.queue.config import QueueConfig
from ...core.queue.monitoring import QueueMonitor, AlertHandler
from ...core.queue.dead_letter import DeadLetterHandler, FailedJobsHandler
from ...core.queue.recovery import FailureRecovery, AutomaticRecovery


router = APIRouter(prefix='/queue', tags=['queue'])


class QueueStatsResponse(BaseModel):
    timestamp: str
    queues: dict
    totals: dict
    health: str
    warnings: list[str]


class QueueDetailsResponse(BaseModel):
    queue_name: str
    pending: int
    active_jobs: list[dict]
    oldest_pending_seconds: Optional[int] = None
    avg_wait_time_seconds: Optional[int] = None


class JobStatusResponse(BaseModel):
    job_id: str
    job_name: str
    status: str
    queue: Optional[str] = None
    attempts: int = 0
    error: Optional[str] = None
    result: Optional[dict] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


@router.get('/stats', response_model=QueueStatsResponse)
async def get_queue_stats():
    pool = await QueueMonitor().get_pool()
    try:
        monitor = QueueMonitor(pool)
        stats = await monitor.get_stats()
        return stats
    finally:
        await pool.aclose()


@router.get('/stats/{queue_name}', response_model=QueueDetailsResponse)
async def get_queue_details(queue_name: str):
    if queue_name not in QueueConfig.QUEUES:
        raise HTTPException(status_code=404, detail=f'Queue {queue_name} not found')

    pool = await QueueMonitor().get_pool()
    try:
        monitor = QueueMonitor(pool)
        details = await monitor.get_queue_details(queue_name)
        return details
    finally:
        await pool.aclose()


@router.get('/worker/status')
async def get_worker_status():
    pool = await QueueMonitor().get_pool()
    try:
        monitor = QueueMonitor(pool)
        status = await monitor.get_worker_status()
        return status
    finally:
        await pool.aclose()


@router.get('/jobs/{job_id}', response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    pool = await QueueMonitor().get_pool()
    try:
        from ...core.queue.base_job import JobTracker
        status = await JobTracker.get_job_status(pool, job_id)
        if not status:
            raise HTTPException(status_code=404, detail=f'Job {job_id} not found')
        return status
    finally:
        await pool.aclose()


@router.get('/jobs', response_model=list[JobStatusResponse])
async def list_jobs(
    queue: Optional[str] = None,
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=50, le=200),
):
    pool = await QueueMonitor().get_pool()
    try:
        monitor = QueueMonitor(pool)
        jobs = await monitor.get_job_history(queue=queue, hours=hours)
        return jobs[:limit]
    finally:
        await pool.aclose()


@router.get('/throughput', response_model=dict)
async def get_throughput(hours: int = Query(default=24, le=168)):
    pool = await QueueMonitor().get_pool()
    try:
        monitor = QueueMonitor(pool)
        stats = await monitor.get_throughput_stats(hours=hours)
        return stats
    finally:
        await pool.aclose()


@router.get('/alerts', response_model=list[dict])
async def get_alerts():
    alerts = await AlertHandler.get_queue_alerts()
    return alerts


@router.get('/health')
async def get_health():
    health = await AlertHandler.check_health()
    return health


@router.get('/slow-jobs')
async def get_slow_jobs(threshold_seconds: int = Query(default=300, ge=60)):
    pool = await QueueMonitor().get_pool()
    try:
        monitor = QueueMonitor(pool)
        jobs = await monitor.get_slow_jobs(threshold_seconds=threshold_seconds)
        return {'count': len(jobs), 'jobs': jobs}
    finally:
        await pool.aclose()


@router.get('/dead-letter', response_model=list[dict])
async def get_dead_letters(
    offset: int = 0,
    limit: int = 50,
    queue_filter: Optional[str] = None,
):
    pool = await DeadLetterHandler().get_pool()
    try:
        handler = DeadLetterHandler(pool)
        items = await handler.get_dead_letters(
            offset=offset,
            limit=limit,
            queue_filter=queue_filter,
        )
        return {'count': len(items), 'items': items}
    finally:
        await pool.aclose()


@router.post('/dead-letter/{job_id}/retry')
async def retry_dead_letter_job(job_id: str):
    pool = await DeadLetterHandler().get_pool()
    try:
        handler = DeadLetterHandler(pool)
        success = await handler.retry_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f'Dead letter job {job_id} not found')
        return {'success': True, 'job_id': job_id}
    finally:
        await pool.aclose()


@router.post('/dead-letter/retry-all')
async def retry_all_dead_letters(queue_filter: Optional[str] = None):
    pool = await DeadLetterHandler().get_pool()
    try:
        handler = DeadLetterHandler(pool)
        result = await handler.retry_all(queue_filter=queue_filter)
        return result
    finally:
        await pool.aclose()


@router.delete('/dead-letter/{job_id}')
async def discard_dead_letter_job(job_id: str):
    pool = await DeadLetterHandler().get_pool()
    try:
        handler = DeadLetterHandler(pool)
        success = await handler.discard_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f'Dead letter job {job_id} not found')
        return {'success': True, 'job_id': job_id}
    finally:
        await pool.aclose()


@router.delete('/dead-letter/purge')
async def purge_dead_letters(queue_filter: Optional[str] = None):
    pool = await DeadLetterHandler().get_pool()
    try:
        handler = DeadLetterHandler(pool)
        count = await handler.discard_all(queue_filter=queue_filter)
        return {'purged_count': count}
    finally:
        await pool.aclose()


@router.get('/failed', response_model=list[dict])
async def get_failed_jobs(
    offset: int = 0,
    limit: int = 50,
    job_name_filter: Optional[str] = None,
):
    pool = await FailedJobsHandler().get_pool()
    try:
        handler = FailedJobsHandler(pool)
        items = await handler.get_failed_jobs(
            offset=offset,
            limit=limit,
            job_name_filter=job_name_filter,
        )
        return {'count': len(items), 'items': items}
    finally:
        await pool.aclose()


@router.get('/failed/stats')
async def get_failed_stats():
    pool = await FailedJobsHandler().get_pool()
    try:
        handler = FailedJobsHandler(pool)
        stats = await handler.get_failed_stats()
        return stats
    finally:
        await pool.aclose()


@router.post('/failed/{job_id}/retry')
async def retry_failed_job(job_id: str):
    pool = await FailedJobsHandler().get_pool()
    try:
        handler = FailedJobsHandler(pool)
        success = await handler.retry_failed_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f'Failed job {job_id} not found')
        return {'success': True, 'job_id': job_id}
    finally:
        await pool.aclose()


@router.delete('/failed/cleanup')
async def cleanup_failed_jobs(older_than_days: int = Query(default=30, ge=1)):
    pool = await FailedJobsHandler().get_pool()
    try:
        handler = FailedJobsHandler(pool)
        cleared = await handler.clear_failed_jobs(older_than_days=older_than_days)
        return {'cleared': cleared, 'older_than_days': older_than_days}
    finally:
        await pool.aclose()


@router.post('/recovery/stuck-jobs')
async def recover_stuck_jobs(timeout_seconds: int = Query(default=3600, ge=60)):
    pool = await FailureRecovery().get_pool()
    try:
        recovery = FailureRecovery(pool)
        result = await recovery.recover_stuck_jobs(timeout_seconds=timeout_seconds)
        return result
    finally:
        await pool.aclose()


@router.post('/recovery/retry-by-error')
async def recover_by_error(
    error_substring: str,
    target_queue: Optional[str] = None,
):
    pool = await FailureRecovery().get_pool()
    try:
        recovery = FailureRecovery(pool)
        result = await recovery.recover_by_error_type(error_substring, target_queue)
        return result
    finally:
        await pool.aclose()


@router.post('/recovery/bulk-recover')
async def bulk_recover_dead_letters(
    older_than_hours: int = Query(default=24, ge=1),
    max_recover: int = Query(default=100, ge=1),
    queue_filter: Optional[str] = None,
):
    pool = await FailureRecovery().get_pool()
    try:
        recovery = FailureRecovery(pool)
        result = await recovery.bulk_recover_dead_letters(
            older_than_hours=older_than_hours,
            max_recover=max_recover,
            queue_filter=queue_filter,
        )
        return result
    finally:
        await pool.aclose()


@router.post('/recovery/reset-stats')
async def reset_queue_stats(queue: Optional[str] = None):
    pool = await FailureRecovery().get_pool()
    try:
        recovery = FailureRecovery(pool)
        result = await recovery.reset_queue_stats(queue=queue)
        return result
    finally:
        await pool.aclose()


@router.get('/recovery/history')
async def get_recovery_history(limit: int = 50):
    pool = await FailureRecovery().get_pool()
    try:
        recovery = FailureRecovery(pool)
        history = await recovery.get_recovery_history(limit=limit)
        return {'count': len(history), 'items': history}
    finally:
        await pool.aclose()


@router.get('/recovery/health')
async def get_system_health():
    auto = AutomaticRecovery()
    health = await auto.get_system_health()
    return health


@router.post('/recovery/run')
async def run_maintenance():
    auto = AutomaticRecovery()
    result = await auto.run_scheduled_recovery()
    return result