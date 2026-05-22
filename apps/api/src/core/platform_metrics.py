"""Platform-wide metrics for the super-admin console (database-backed)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import QueueJob, UsageLog, User


def _utc_today_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def queue_job_to_admin_dict(job: QueueJob) -> dict[str, Any]:
    created = job.created_at or datetime.now(timezone.utc)
    started = job.started_at
    progress = 100 if job.status == 'completed' else (50 if job.status == 'processing' else 0)
    priority = 'high' if (job.priority or 0) > 5 else 'normal'
    return {
        'id': str(job.id),
        'name': (job.job_type or 'job').replace('_', ' ').title(),
        'status': job.status,
        'progress': progress,
        'priority': priority,
        'queue': job.job_type or 'default',
        'worker': None,
        'attempts': job.attempts or 0,
        'maxAttempts': job.max_attempts or 3,
        'createdAt': created.isoformat(),
        'startedAt': started.isoformat() if started else None,
        'error': job.error,
        'payload': job.payload or {},
    }


def failed_queue_job_to_admin_dict(job: QueueJob) -> dict[str, Any]:
    ts = (job.updated_at or job.created_at or datetime.now(timezone.utc)).isoformat()
    return {
        'id': str(job.id),
        'jobName': (job.job_type or 'Job').replace('_', ' ').title(),
        'queue': job.job_type or 'unknown',
        'failedAt': ts,
        'error': job.error or 'Job failed',
        'attemptCount': job.attempts or 0,
        'lastAttemptAt': ts,
        'retryable': (job.attempts or 0) < (job.max_attempts or 3),
        'payload': job.payload or {},
    }


async def load_platform_queue_jobs(db: AsyncSession, *, limit: int = 100) -> list[dict[str, Any]]:
    result = await db.execute(
        select(QueueJob).order_by(QueueJob.created_at.desc()).limit(limit)
    )
    return [queue_job_to_admin_dict(job) for job in result.scalars().all()]


async def load_platform_failed_jobs(
    db: AsyncSession,
    dismissed: set[str],
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(QueueJob)
        .where(QueueJob.status == 'failed')
        .order_by(QueueJob.created_at.desc())
        .limit(limit)
    )
    jobs: list[dict[str, Any]] = []
    for job in result.scalars().all():
        jid = str(job.id)
        if jid not in dismissed:
            jobs.append(failed_queue_job_to_admin_dict(job))
    return jobs


async def append_email_queue_jobs(db: AsyncSession, jobs: list[dict[str, Any]], *, limit: int = 50) -> None:
    try:
        from .email.db_models import EmailQueueItem
    except Exception:
        return

    result = await db.execute(
        select(EmailQueueItem).order_by(EmailQueueItem.created_at.desc()).limit(limit)
    )
    for item in result.scalars().all():
        jobs.append(
            {
                'id': str(item.id),
                'name': f'Email: {item.event_key or "notification"}',
                'status': item.status,
                'progress': 100 if item.status == 'completed' else 0,
                'priority': 'normal',
                'queue': 'email',
                'attempts': item.retry_count or 0,
                'maxAttempts': item.max_retries or 5,
                'createdAt': (item.created_at or datetime.now(timezone.utc)).isoformat(),
                'error': item.last_error,
                'payload': {'recipient': item.recipient_email},
            }
        )


async def append_email_failed_jobs(
    db: AsyncSession,
    jobs: list[dict[str, Any]],
    dismissed: set[str],
) -> None:
    try:
        from .email.db_models import EmailQueueItem
    except Exception:
        return

    result = await db.execute(
        select(EmailQueueItem)
        .where(EmailQueueItem.status.in_(('failed', 'dead_letter')))
        .order_by(EmailQueueItem.updated_at.desc())
        .limit(100)
    )
    for item in result.scalars().all():
        jid = str(item.id)
        if jid in dismissed:
            continue
        jobs.append(
            {
                'id': jid,
                'jobName': f'Email: {item.event_key}',
                'queue': 'email',
                'failedAt': (item.updated_at or item.created_at).isoformat(),
                'error': item.last_error or 'Delivery failed',
                'attemptCount': item.retry_count or 0,
                'lastAttemptAt': (item.updated_at or item.created_at).isoformat(),
                'retryable': item.status != 'dead_letter',
                'payload': {'recipient': item.recipient_email},
            }
        )


async def platform_analytics_summary(db: AsyncSession, *, usage_days: int = 7) -> dict[str, Any]:
    today_start = _utc_today_start()
    month_start = datetime.now(timezone.utc) - timedelta(days=30)
    usage_since = datetime.now(timezone.utc) - timedelta(days=usage_days)

    user_count = await db.scalar(select(func.count()).select_from(User)) or 0

    api_today = await db.scalar(
        select(func.count(UsageLog.id)).where(UsageLog.created_at >= today_start)
    ) or 0

    active_jobs = await db.scalar(
        select(func.count(QueueJob.id)).where(QueueJob.status.in_(('pending', 'processing')))
    ) or 0

    failed = await db.scalar(
        select(func.count(QueueJob.id)).where(QueueJob.status == 'failed')
    ) or 0
    completed = await db.scalar(
        select(func.count(QueueJob.id)).where(QueueJob.status == 'completed')
    ) or 0

    try:
        from .email.db_models import EmailQueueItem

        email_active = await db.scalar(
            select(func.count(EmailQueueItem.id)).where(
                EmailQueueItem.status.in_(('pending', 'processing', 'queued'))
            )
        ) or 0
        active_jobs += int(email_active)
        email_failed = await db.scalar(
            select(func.count(EmailQueueItem.id)).where(
                EmailQueueItem.status.in_(('failed', 'dead_letter'))
            )
        ) or 0
        failed += int(email_failed)
        email_ok = await db.scalar(
            select(func.count(EmailQueueItem.id)).where(EmailQueueItem.status == 'completed')
        ) or 0
        completed += int(email_ok)
    except Exception:
        pass

    failure_rate = failed / max(completed + failed, 1)

    monthly_cost = float(
        await db.scalar(
            select(func.coalesce(func.sum(UsageLog.cost_usd), 0.0)).where(
                UsageLog.created_at >= month_start
            )
        )
        or 0.0
    )

    usage_rows = await db.execute(
        select(
            func.date(UsageLog.created_at).label('day'),
            func.count(UsageLog.id).label('api_calls'),
            func.coalesce(
                func.sum(case((UsageLog.resource_type == 'document', 1), else_=0)),
                0,
            ).label('documents'),
            func.coalesce(func.sum(UsageLog.tokens_used), 0).label('tokens'),
            func.coalesce(func.sum(UsageLog.cost_usd), 0.0).label('cost'),
        )
        .where(UsageLog.created_at >= usage_since)
        .group_by(func.date(UsageLog.created_at))
        .order_by(func.date(UsageLog.created_at))
    )

    usage: list[dict[str, Any]] = []
    for row in usage_rows.all():
        day = row.day
        date_str = day.isoformat() if hasattr(day, 'isoformat') else str(day)
        usage.append(
            {
                'date': date_str,
                'apiCalls': int(row.api_calls or 0),
                'documentsProcessed': int(row.documents or 0),
                'tokensUsed': int(row.tokens or 0),
                'cost': round(float(row.cost or 0.0), 4),
            }
        )

    return {
        'dataSource': 'database',
        'scope': 'platform',
        'totalUsers': int(user_count),
        'apiCallsToday': int(api_today),
        'activeJobs': int(active_jobs),
        'errorRate': round(failure_rate * 100, 1),
        'avgResponseTime': 0.0,
        'monthlyCost': round(monthly_cost, 2),
        'usage': usage,
    }
