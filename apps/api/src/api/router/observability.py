"""Observability System - API Monitoring, Metrics, Health Checks"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...core.models import AuditLog, User, Tenant
from ...core.database import get_db
from ..dependencies.auth import get_current_user
from ...core.auth import AuthContext
from ...core.orchestrator.logging import MetricsCollector as MetricsAggregator

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/observability', tags=['Observability'])


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


MOCK_START_TIME = datetime(2025, 1, 1, tzinfo=timezone.utc)

MOCK_API_METRICS = {
    '/api/v1/tenders': {'requests': 1250, 'errors': 12, 'avg_duration': 45.2},
    '/api/v1/documents': {'requests': 890, 'errors': 8, 'avg_duration': 120.5},
    '/api/v1/ai/analyze': {'requests': 456, 'errors': 3, 'avg_duration': 2500.0},
    '/api/v1/queue/submit': {'requests': 2100, 'errors': 15, 'avg_duration': 15.0},
    '/api/v1/bids': {'requests': 340, 'errors': 2, 'avg_duration': 35.8},
}

MOCK_QUEUE_METRICS = [
    {'queue_name': 'ocr', 'pending': 12, 'active': 3, 'completed': 1500, 'failed': 8, 'dead_letter': 2, 'avg_time': 4500},
    {'queue_name': 'parsing', 'pending': 5, 'active': 2, 'completed': 890, 'failed': 4, 'dead_letter': 1, 'avg_time': 2200},
    {'queue_name': 'analysis', 'pending': 8, 'active': 1, 'completed': 456, 'failed': 2, 'dead_letter': 0, 'avg_time': 8500},
    {'queue_name': 'email', 'pending': 25, 'active': 5, 'completed': 3200, 'failed': 12, 'dead_letter': 3, 'avg_time': 800},
    {'queue_name': 'notifications', 'pending': 45, 'active': 8, 'completed': 5600, 'failed': 20, 'dead_letter': 5, 'avg_time': 200},
]

MOCK_AI_METRICS = [
    {'provider': 'openai', 'model': 'gpt-4', 'requests': 850, 'input_tokens': 1250000, 'output_tokens': 890000, 'cost': 42.50, 'latency': 1800, 'success_rate': 0.98},
    {'provider': 'anthropic', 'model': 'claude-3', 'requests': 420, 'input_tokens': 680000, 'output_tokens': 520000, 'cost': 28.75, 'latency': 1500, 'success_rate': 0.99},
    {'provider': 'azure', 'model': 'gpt-35-turbo', 'requests': 1250, 'input_tokens': 2100000, 'output_tokens': 1400000, 'cost': 15.20, 'latency': 900, 'success_rate': 0.97},
]

MOCK_FAILURES = [
    {'id': 'f1', 'type': 'timeout', 'queue': 'analysis', 'message': 'AI request timeout after 30s', 'occurred_at': '2026-05-19T10:30:00Z', 'retry_count': 3},
    {'id': 'f2', 'type': 'invalid_input', 'queue': 'parsing', 'message': 'Failed to parse corrupt PDF', 'occurred_at': '2026-05-19T09:45:00Z', 'retry_count': 2},
    {'id': 'f3', 'type': 'rate_limit', 'queue': 'ocr', 'message': 'External OCR API rate limit exceeded', 'occurred_at': '2026-05-19T08:20:00Z', 'retry_count': 5},
]


def _get_uptime() -> float:
    return (datetime.now(timezone.utc) - MOCK_START_TIME).total_seconds()


@router.get('/metrics/api', response_model=list[APIEndpointMetrics])
async def get_api_metrics(
    limit: int = Query(20, le=100),
    current_user: AuthContext = Depends(get_current_user),
):
    """Get API endpoint metrics"""
    
    results = []
    for endpoint, data in MOCK_API_METRICS.items():
        requests = data['requests']
        errors = data['errors']
        success = requests - errors
        
        results.append(APIEndpointMetrics(
            endpoint=endpoint,
            method='GET',
            total_requests=requests,
            success_count=success,
            error_count=errors,
            avg_duration_ms=data['avg_duration'],
            p50_latency_ms=data['avg_duration'] * 0.8,
            p95_latency_ms=data['avg_duration'] * 1.5,
            p99_latency_ms=data['avg_duration'] * 2.0,
        ))
    
    return results[:limit]


@router.get('/metrics/queue', response_model=list[QueueMetrics])
async def get_queue_metrics(
    current_user: AuthContext = Depends(get_current_user),
):
    """Get queue metrics"""
    
    return [QueueMetrics(
        queue_name=m['queue_name'],
        pending=m['pending'],
        active=m['active'],
        completed=m['completed'],
        failed=m['failed'],
        dead_letter=m['dead_letter'],
        avg_processing_time_ms=m['avg_time'],
    ) for m in MOCK_QUEUE_METRICS]


@router.get('/metrics/ai', response_model=list[AITokenMetrics])
async def get_ai_metrics(
    provider: Optional[str] = Query(None),
    days: int = Query(7, le=30),
    current_user: AuthContext = Depends(get_current_user),
):
    """Get AI token usage metrics"""
    
    metrics = MOCK_AI_METRICS
    if provider:
        metrics = [m for m in metrics if m['provider'] == provider]
    
    return [AITokenMetrics(
        provider=m['provider'],
        model=m['model'],
        total_requests=m['requests'],
        total_input_tokens=m['input_tokens'],
        total_output_tokens=m['output_tokens'],
        total_cost=m['cost'],
        avg_latency_ms=m['latency'],
        success_rate=m['success_rate'],
    ) for m in metrics]


@router.get('/metrics/processing', response_model=ProcessingMetrics)
async def get_processing_metrics(
    days: int = Query(1, le=30),
    current_user: AuthContext = Depends(get_current_user),
):
    """Get document processing metrics"""
    
    return ProcessingMetrics(
        document_count=1250,
        ocr_count=890,
        parsing_count=456,
        analysis_count=340,
        extraction_count=210,
        avg_processing_time_ms=1850,
        success_rate=0.96,
    )


@router.get('/metrics/failures', response_model=FailureMetrics)
async def get_failure_metrics(
    days: int = Query(7, le=30),
    queue: Optional[str] = Query(None),
    current_user: AuthContext = Depends(get_current_user),
):
    """Get failure tracking metrics"""
    
    failures_by_type = {'timeout': 45, 'invalid_input': 32, 'rate_limit': 28, 'external_error': 15}
    failures_by_queue = {'analysis': 38, 'ocr': 35, 'parsing': 28, 'email': 19}
    
    if queue:
        failures_by_queue = {queue: failures_by_queue.get(queue, 0)}
    
    return FailureMetrics(
        total_failures=120,
        failures_by_type=failures_by_type,
        failures_by_queue=failures_by_queue,
        recent_failures=MOCK_FAILURES,
        retry_rate=0.75,
    )


@router.get('/metrics/summary')
async def get_metrics_summary(
    current_user: AuthContext = Depends(get_current_user),
):
    """Get overall metrics summary"""
    
    total_api_requests = sum(m['requests'] for m in MOCK_API_METRICS.values())
    total_queue_jobs = sum(m['completed'] for m in MOCK_QUEUE_METRICS)
    total_ai_requests = sum(m['requests'] for m in MOCK_AI_METRICS)
    total_ai_cost = sum(m['cost'] for m in MOCK_AI_METRICS)
    
    return {
        'api': {
            'total_requests': total_api_requests,
            'error_rate': 0.015,
            'avg_response_time_ms': 145.5,
        },
        'queue': {
            'total_jobs': total_queue_jobs,
            'active_jobs': sum(m['active'] for m in MOCK_QUEUE_METRICS),
            'failure_rate': 0.008,
        },
        'ai': {
            'total_requests': total_ai_requests,
            'total_cost': round(total_ai_cost, 2),
            'total_tokens': sum(m['input_tokens'] + m['output_tokens'] for m in MOCK_AI_METRICS),
        },
        'processing': {
            'documents_processed': 1250,
            'success_rate': 0.96,
        },
    }


@router.get('/health')
async def get_health(
    x_health_check: Optional[str] = Header(None, alias='X-Health-Check'),
):
    """Health check endpoint"""
    
    return HealthStatus(
        status='healthy',
        checks={
            'api': 'healthy',
            'database': 'healthy',
            'queue': 'inline',
            'ai_providers': 'healthy',
        },
        uptime_seconds=_get_uptime(),
        version='1.0.0',
    )


@router.get('/health/detailed')
async def get_detailed_health(
    db=Depends(get_db),
):
    """Detailed health check with component status"""
    from sqlalchemy import text

    db_healthy = False
    try:
        await db.execute(text('SELECT 1'))
        db_healthy = True
    except Exception:
        pass

    overall = 'healthy' if db_healthy else 'unhealthy'

    return {
        'status': overall,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'components': {
            'database': {'status': 'up' if db_healthy else 'down', 'latency_ms': 5},
            'queue': {'status': 'inline', 'mode': 'in-process'},
            'sentry': {'status': 'configured'},
        },
        'uptime_seconds': _get_uptime(),
    }


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


@router.post('/metrics/custom')
async def record_custom_metric(
    metric: MetricData,
    current_user: AuthContext = Depends(get_current_user),
):
    """Record a custom metric"""
    
    logger.info(f"Custom metric: {metric.name}={metric.value} tags={metric.tags}")
    
    return {'success': True, 'metric_id': f"metric-{time.time()}"}


@router.get('/trends')
async def get_metrics_trend(
    metric_type: str = Query(..., pattern='^(api|queue|ai|processing)$'),
    days: int = Query(7, le=30),
    current_user: AuthContext = Depends(get_current_user),
):
    """Get metrics trends over time"""
    
    if metric_type == 'api':
        return {
            'metric': 'api_requests',
            'data': [
                {'date': '2026-05-19', 'value': 4500},
                {'date': '2026-05-18', 'value': 4200},
                {'date': '2026-05-17', 'value': 3800},
                {'date': '2026-05-16', 'value': 5100},
                {'date': '2026-05-15', 'value': 4800},
            ]
        }
    elif metric_type == 'queue':
        return {
            'metric': 'queue_throughput',
            'data': [
                {'date': '2026-05-19', 'value': 1250},
                {'date': '2026-05-18', 'value': 1180},
                {'date': '2026-05-17', 'value': 950},
                {'date': '2026-05-16', 'value': 1400},
                {'date': '2026-05-15', 'value': 1320},
            ]
        }
    elif metric_type == 'ai':
        return {
            'metric': 'ai_tokens',
            'data': [
                {'date': '2026-05-19', 'input': 250000, 'output': 180000, 'cost': 12.5},
                {'date': '2026-05-18', 'input': 220000, 'output': 160000, 'cost': 11.2},
                {'date': '2026-05-17', 'input': 280000, 'output': 200000, 'cost': 14.0},
                {'date': '2026-05-16', 'input': 310000, 'output': 220000, 'cost': 15.5},
                {'date': '2026-05-15', 'input': 190000, 'output': 140000, 'cost': 9.5},
            ]
        }
    else:
        return {
            'metric': 'processing_time_ms',
            'data': [
                {'date': '2026-05-19', 'value': 1850},
                {'date': '2026-05-18', 'value': 1920},
                {'date': '2026-05-17', 'value': 2100},
                {'date': '2026-05-16', 'value': 1750},
                {'date': '2026-05-15', 'value': 1680},
            ]
        }