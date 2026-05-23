"""Database-backed tenant and platform observability metrics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import QueueJob, UsageLog

_APP_START_TIME: Optional[datetime] = None


def set_app_start_time(when: Optional[datetime] = None) -> None:
    global _APP_START_TIME
    _APP_START_TIME = when or datetime.now(timezone.utc)


def get_uptime_seconds() -> float:
    start = _APP_START_TIME or datetime.now(timezone.utc)
    return (datetime.now(timezone.utc) - start).total_seconds()


async def compute_queue_failure_rate(
    db: AsyncSession,
    tenant_id: UUID,
    *,
    days: int = 7,
) -> float:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    failed = await db.scalar(
        select(func.count(QueueJob.id)).where(
            QueueJob.tenant_id == tenant_id,
            QueueJob.status == 'failed',
            QueueJob.created_at >= since,
        )
    ) or 0
    completed = await db.scalar(
        select(func.count(QueueJob.id)).where(
            QueueJob.tenant_id == tenant_id,
            QueueJob.status == 'completed',
            QueueJob.created_at >= since,
        )
    ) or 0
    total = failed + completed
    return round(failed / total, 4) if total else 0.0


async def build_tenant_metrics_summary(db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
    total_api = await db.scalar(
        select(func.count(UsageLog.id)).where(UsageLog.tenant_id == tenant_id)
    ) or 0

    cost_row = await db.execute(
        select(func.coalesce(func.sum(UsageLog.cost_usd), 0).label('total')).where(
            UsageLog.tenant_id == tenant_id
        )
    )
    total_cost = float(cost_row.scalar_one() or 0)

    token_row = await db.execute(
        select(func.coalesce(func.sum(UsageLog.tokens_used), 0).label('total')).where(
            UsageLog.tenant_id == tenant_id
        )
    )
    total_tokens = int(token_row.scalar_one() or 0)

    queue_total = await db.scalar(
        select(func.count(QueueJob.id)).where(QueueJob.tenant_id == tenant_id)
    ) or 0

    queue_active = await db.scalar(
        select(func.count(QueueJob.id)).where(
            QueueJob.tenant_id == tenant_id,
            QueueJob.status.in_(('pending', 'processing')),
        )
    ) or 0

    failure_rate = await compute_queue_failure_rate(db, tenant_id)

    since_day = datetime.now(timezone.utc) - timedelta(days=1)
    documents_processed = await db.scalar(
        select(func.count(UsageLog.id)).where(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= since_day,
            UsageLog.resource_type == 'document',
        )
    ) or 0

    doc_success = await db.scalar(
        select(func.count(QueueJob.id)).where(
            QueueJob.tenant_id == tenant_id,
            QueueJob.status == 'completed',
            QueueJob.job_type.in_(('ocr', 'document_parse', 'parsing', 'analysis')),
        )
    ) or 0
    doc_failed = await db.scalar(
        select(func.count(QueueJob.id)).where(
            QueueJob.tenant_id == tenant_id,
            QueueJob.status == 'failed',
            QueueJob.job_type.in_(('ocr', 'document_parse', 'parsing', 'analysis')),
        )
    ) or 0
    proc_total = doc_success + doc_failed
    processing_success = round(doc_success / proc_total, 4) if proc_total else 1.0

    return {
        'success': True,
        'data': {
            'api': {
                'total_requests': int(total_api),
                'error_rate': round(failure_rate * 100, 2),
                'avg_response_time_ms': 0.0,
            },
            'queue': {
                'total_jobs': int(queue_total),
                'active_jobs': int(queue_active),
                'failure_rate': round(failure_rate * 100, 2),
            },
            'ai': {
                'total_requests': int(total_api),
                'total_cost': round(total_cost, 2),
                'total_tokens': int(total_tokens),
            },
            'processing': {
                'documents_processed': int(documents_processed),
                'success_rate': round(processing_success * 100, 2),
            },
        },
    }


async def build_detailed_health(db: AsyncSession, *, version: str) -> dict[str, Any]:
    from sqlalchemy import text

    db_healthy = False
    latency_ms = 0.0
    started = datetime.now(timezone.utc)
    try:
        await db.execute(text('SELECT 1'))
        db_healthy = True
        latency_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
    except Exception:
        pass

    overall = 'healthy' if db_healthy else 'unhealthy'

    return {
        'status': overall,
        'canonical_health_path': '/health',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'components': {
            'database': {'status': 'up' if db_healthy else 'down', 'latency_ms': round(latency_ms, 2)},
            'queue': {'status': 'inline', 'mode': 'in-process'},
            'sentry': {'status': 'configured'},
        },
        'uptime_seconds': get_uptime_seconds(),
        'version': version,
    }
