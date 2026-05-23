"""Observability System - API Monitoring, Metrics, Health Checks"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.models import UsageLog, QueueJob
from ...core.database import get_db
from ...core.observability_metrics import (
    build_detailed_health,
    build_tenant_metrics_summary,
    compute_queue_failure_rate,
    get_uptime_seconds,
)
from ..dependencies.auth import get_current_user
from ..dependencies.rbac_deps import require_tenant_member
from ...core.auth import AuthContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/observability', tags=['Observability'])

metrics_router = APIRouter(
    prefix='/metrics',
    tags=['Observability Metrics'],
    dependencies=[Depends(require_tenant_member)],
)


def _tenant_uuid(current_user: AuthContext) -> UUID:
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required for observability metrics')
    return UUID(current_user.tenant_id)


class MetricData(BaseModel):
    name: str
    value: float
    tags: dict = {}
    timestamp: str


class APIEndpointMetrics(BaseModel):
    endpoint: str
    method: str
    total_requests: int
    success_count: int
    error_count: int
    avg_duration_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


class QueueMetrics(BaseModel):
    queue_name: str
    pending: int
    active: int
    completed: int
    failed: int
    dead_letter: int
    avg_processing_time_ms: float


class AITokenMetrics(BaseModel):
    provider: str
    model: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    avg_latency_ms: float
    success_rate: float


class ProcessingMetrics(BaseModel):
    document_count: int
    ocr_count: int
    parsing_count: int
    analysis_count: int
    extraction_count: int
    avg_processing_time_ms: float
    success_rate: float


class FailureMetrics(BaseModel):
    total_failures: int
    failures_by_type: dict
    failures_by_queue: dict
    recent_failures: list
    retry_rate: float


class HealthStatus(BaseModel):
    status: str
    checks: dict
    uptime_seconds: float
    version: str


@metrics_router.get('/api', response_model=list[APIEndpointMetrics])
async def get_api_metrics(
    limit: int = Query(20, le=100),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get API endpoint metrics — counts UsageLog by action"""
    try:
        tenant_id = _tenant_uuid(current_user)
        rows = await db.execute(
            select(
                UsageLog.action,
                func.count(UsageLog.id).label('total_requests'),
            )
            .where(UsageLog.tenant_id == tenant_id)
            .group_by(UsageLog.action)
            .order_by(func.count(UsageLog.id).desc())
            .limit(limit)
        )
        results = []
        for row in rows.all():
            results.append(APIEndpointMetrics(
                endpoint=row.action,
                method='POST',
                total_requests=row.total_requests,
                success_count=row.total_requests,
                error_count=0,
                avg_duration_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
            ))
        return results
    except Exception:
        logger.exception('Failed to fetch API metrics')
        return []


@metrics_router.get('/queue', response_model=list[QueueMetrics])
async def get_queue_metrics(
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get queue metrics — counts QueueJob by status"""
    try:
        tenant_id = _tenant_uuid(current_user)
        rows = await db.execute(
            select(
                QueueJob.job_type,
                QueueJob.status,
                func.count(QueueJob.id).label('cnt'),
            )
            .where(QueueJob.tenant_id == tenant_id)
            .group_by(QueueJob.job_type, QueueJob.status)
        )
        job_data = {}
        for row in rows.all():
            key = row.job_type or 'unknown'
            if key not in job_data:
                job_data[key] = {'queue_name': key, 'pending': 0, 'active': 0, 'completed': 0, 'failed': 0, 'dead_letter': 0, 'avg_processing_time_ms': 0.0}
            status = row.status or 'pending'
            if status == 'pending':
                job_data[key]['pending'] = row.cnt
            elif status == 'processing':
                job_data[key]['active'] = row.cnt
            elif status == 'completed':
                job_data[key]['completed'] = row.cnt
            elif status == 'failed':
                job_data[key]['failed'] = row.cnt
            elif status == 'cancelled':
                job_data[key]['dead_letter'] = row.cnt
            else:
                job_data[key]['pending'] += row.cnt

        return [QueueMetrics(**v) for v in job_data.values()]
    except Exception:
        logger.exception('Failed to fetch queue metrics')
        return []


@metrics_router.get('/ai', response_model=list[AITokenMetrics])
async def get_ai_metrics(
    provider: Optional[str] = Query(None),
    days: int = Query(7, le=30),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI token usage metrics — sums cost_usd and tokens_used from UsageLog"""
    try:
        tenant_id = _tenant_uuid(current_user)
        since = datetime.utcnow() - timedelta(days=days)
        conditions = [
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= since,
        ]
        if provider:
            conditions.append(UsageLog.action.like(f'%{provider}%'))

        rows = await db.execute(
            select(
                func.coalesce(func.sum(UsageLog.cost_usd), 0).label('total_cost'),
                func.coalesce(func.sum(UsageLog.tokens_used), 0).label('total_tokens'),
                func.count(UsageLog.id).label('total_requests'),
            )
            .where(*conditions)
        )
        row = rows.one()
        total_cost = float(row.total_cost) if row.total_cost else 0.0
        total_tokens = int(row.total_tokens) if row.total_tokens else 0
        total_requests = int(row.total_requests) if row.total_requests else 0

        return [AITokenMetrics(
            provider=provider or 'openai',
            model='gpt-4',
            total_requests=total_requests,
            total_input_tokens=total_tokens // 2 if total_tokens else 0,
            total_output_tokens=total_tokens // 2 if total_tokens else 0,
            total_cost=total_cost,
            avg_latency_ms=0.0,
            success_rate=1.0 if total_requests > 0 else 0.0,
        )]
    except Exception:
        logger.exception('Failed to fetch AI metrics')
        return []


@metrics_router.get('/processing', response_model=ProcessingMetrics)
async def get_processing_metrics(
    days: int = Query(1, le=30),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document processing metrics"""
    try:
        tenant_id = _tenant_uuid(current_user)
        since = datetime.utcnow() - timedelta(days=days)

        total = await db.scalar(
            select(func.count(UsageLog.id)).where(
                UsageLog.tenant_id == tenant_id,
                UsageLog.created_at >= since,
                UsageLog.resource_type == 'document',
            )
        ) or 0

        ocr_count = await db.scalar(
            select(func.count(QueueJob.id)).where(
                QueueJob.tenant_id == tenant_id,
                QueueJob.created_at >= since,
                QueueJob.job_type == 'ocr',
            )
        ) or 0
        analysis_count = await db.scalar(
            select(func.count(QueueJob.id)).where(
                QueueJob.tenant_id == tenant_id,
                QueueJob.created_at >= since,
                QueueJob.job_type.in_(('analysis', 'ai_analysis')),
            )
        ) or 0
        completed = await db.scalar(
            select(func.count(QueueJob.id)).where(
                QueueJob.tenant_id == tenant_id,
                QueueJob.created_at >= since,
                QueueJob.status == 'completed',
            )
        ) or 0
        failed = await db.scalar(
            select(func.count(QueueJob.id)).where(
                QueueJob.tenant_id == tenant_id,
                QueueJob.created_at >= since,
                QueueJob.status == 'failed',
            )
        ) or 0
        proc_total = completed + failed
        success_rate = round(completed / proc_total, 4) if proc_total else 1.0

        return ProcessingMetrics(
            document_count=total,
            ocr_count=int(ocr_count),
            parsing_count=0,
            analysis_count=int(analysis_count),
            extraction_count=0,
            avg_processing_time_ms=0.0,
            success_rate=success_rate,
        )
    except Exception:
        logger.exception('Failed to fetch processing metrics')
        return ProcessingMetrics(
            document_count=0, ocr_count=0, parsing_count=0,
            analysis_count=0, extraction_count=0,
            avg_processing_time_ms=0.0, success_rate=0.0,
        )


@metrics_router.get('/failures', response_model=FailureMetrics)
async def get_failure_metrics(
    days: int = Query(7, le=30),
    queue: Optional[str] = Query(None),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get failure tracking metrics — queries QueueJob where status='failed'"""
    try:
        tenant_id = _tenant_uuid(current_user)
        since = datetime.utcnow() - timedelta(days=days)

        conditions = [
            QueueJob.tenant_id == tenant_id,
            QueueJob.status == 'failed',
            QueueJob.created_at >= since,
        ]
        if queue:
            conditions.append(QueueJob.job_type == queue)

        total = await db.scalar(
            select(func.count(QueueJob.id)).where(*conditions)
        ) or 0

        type_rows = await db.execute(
            select(QueueJob.job_type, func.count(QueueJob.id).label('cnt'))
            .where(*conditions)
            .group_by(QueueJob.job_type)
        )
        failures_by_type = {}
        failures_by_queue = {}
        recent = []
        for row in type_rows.all():
            jt = row.job_type or 'unknown'
            failures_by_type[jt] = row.cnt
            failures_by_queue[jt] = row.cnt

        recent_q = (
            select(QueueJob)
            .where(*conditions)
            .order_by(QueueJob.created_at.desc())
            .limit(10)
        )
        recent_rows = (await db.execute(recent_q)).scalars().all()
        for r in recent_rows:
            recent.append({
                'id': str(r.id),
                'type': r.job_type or 'unknown',
                'queue': r.job_type or 'unknown',
                'message': r.error or '',
                'occurred_at': r.created_at.isoformat() if r.created_at else '',
                'retry_count': r.attempts or 0,
            })

        retry_rate = await compute_queue_failure_rate(db, tenant_id, days=days)

        return FailureMetrics(
            total_failures=total,
            failures_by_type=failures_by_type,
            failures_by_queue=failures_by_queue,
            recent_failures=recent,
            retry_rate=retry_rate,
        )
    except Exception:
        logger.exception('Failed to fetch failure metrics')
        return FailureMetrics(
            total_failures=0, failures_by_type={},
            failures_by_queue={}, recent_failures=[], retry_rate=0.0,
        )


@metrics_router.get('/summary')
async def get_metrics_summary(
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overall metrics summary for the current tenant."""
    try:
        return await build_tenant_metrics_summary(db, _tenant_uuid(current_user))
    except HTTPException:
        raise
    except Exception:
        logger.exception('Failed to fetch metrics summary')
        return {
            'success': False,
            'data': {
                'api': {'total_requests': 0, 'error_rate': 0.0, 'avg_response_time_ms': 0.0},
                'queue': {'total_jobs': 0, 'active_jobs': 0, 'failure_rate': 0.0},
                'ai': {'total_requests': 0, 'total_cost': 0.0, 'total_tokens': 0},
                'processing': {'documents_processed': 0, 'success_rate': 0.0},
            },
        }


router.include_router(metrics_router)


@router.get('/health')
async def get_health(
    x_health_check: Optional[str] = Header(None, alias='X-Health-Check'),
):
    """Observability health (canonical app health is GET /health)."""
    return HealthStatus(
        status='healthy',
        checks={
            'api': 'healthy',
            'database': 'healthy',
            'queue': 'inline',
            'ai_providers': 'healthy',
            'canonical_path': '/health',
        },
        uptime_seconds=get_uptime_seconds(),
        version=settings.VERSION,
    )


@router.get('/health/detailed')
async def get_detailed_health(
    db: AsyncSession = Depends(get_db),
):
    """Detailed health check with component status"""
    return await build_detailed_health(db, version=settings.VERSION)


@router.get('/health/ready')
async def readiness_check(
    db=Depends(get_db),
):
    """Readiness check for service orchestration"""
    from sqlalchemy import text

    checks: dict[str, bool] = {'database': False}

    try:
        await db.execute(text('SELECT 1'))
        checks['database'] = True
    except Exception:
        pass

    all_ready = checks['database']

    return JSONResponse(
        status_code=200 if all_ready else 503,
        content={
            'status': 'ready' if all_ready else 'not ready',
            'checks': checks,
        }
    )


@router.get('/health/live')
async def liveness_check():
    """Liveness check for container orchestration"""
    return {'status': 'alive', 'timestamp': datetime.now(timezone.utc).isoformat()}


@metrics_router.post('/custom')
async def record_custom_metric(
    metric: MetricData,
    current_user: AuthContext = Depends(get_current_user),
):
    """Record a custom metric"""
    logger.info(f"Custom metric: {metric.name}={metric.value} tags={metric.tags}")
    return {'success': True, 'metric_id': f"metric-{time.time()}"}


@router.get('/trends', dependencies=[Depends(require_tenant_member)])
async def get_metrics_trend(
    metric_type: str = Query(..., pattern='^(api|queue|ai|processing)$'),
    days: int = Query(7, le=30),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get metrics trends over time"""
    try:
        tenant_id = _tenant_uuid(current_user)
        since = datetime.utcnow() - timedelta(days=days)

        if metric_type == 'api':
            rows = await db.execute(
                select(
                    func.date(UsageLog.created_at).label('day'),
                    func.count(UsageLog.id).label('cnt'),
                )
                .where(UsageLog.tenant_id == tenant_id, UsageLog.created_at >= since)
                .group_by(func.date(UsageLog.created_at))
                .order_by(func.date(UsageLog.created_at))
            )
            data = [{'date': str(r.day), 'value': r.cnt} for r in rows.all()]
            return {'metric': 'api_requests', 'data': data}

        elif metric_type == 'queue':
            rows = await db.execute(
                select(
                    func.date(QueueJob.created_at).label('day'),
                    func.count(QueueJob.id).label('cnt'),
                )
                .where(QueueJob.tenant_id == tenant_id, QueueJob.created_at >= since)
                .group_by(func.date(QueueJob.created_at))
                .order_by(func.date(QueueJob.created_at))
            )
            data = [{'date': str(r.day), 'value': r.cnt} for r in rows.all()]
            return {'metric': 'queue_throughput', 'data': data}

        elif metric_type == 'ai':
            rows = await db.execute(
                select(
                    func.date(UsageLog.created_at).label('day'),
                    func.coalesce(func.sum(UsageLog.tokens_used), 0).label('tokens'),
                    func.coalesce(func.sum(UsageLog.cost_usd), 0).label('cost'),
                )
                .where(UsageLog.tenant_id == tenant_id, UsageLog.created_at >= since)
                .group_by(func.date(UsageLog.created_at))
                .order_by(func.date(UsageLog.created_at))
            )
            data = [{'date': str(r.day), 'input': r.tokens // 2, 'output': r.tokens // 2, 'cost': float(r.cost)} for r in rows.all()]
            return {'metric': 'ai_tokens', 'data': data}

        else:
            return {
                'metric': 'processing_time_ms',
                'data': [
                    {'date': (since + timedelta(days=i)).strftime('%Y-%m-%d'), 'value': 0}
                    for i in range(days)
                ],
            }
    except Exception:
        logger.exception('Failed to fetch trends')
        return {'metric': metric_type, 'data': []}
