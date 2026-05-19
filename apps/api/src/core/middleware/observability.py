"""Observability Middleware - API Request Monitoring and Metrics"""

import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..redis import get_redis

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and store API metrics in Redis"""
    
    METRICS_KEY_PREFIX = 'metrics:api'
    
    @staticmethod
    async def record_request(
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Record an API request metric"""
        
        try:
            redis = await get_redis()
            
            now = datetime.now(timezone.utc)
            date_key = now.strftime('%Y-%m-%d')
            minute_key = now.strftime('%Y-%m-%d:%H:%M')
            
            base_key = f"{MetricsCollector.METRICS_KEY_PREFIX}:{date_key}"
            
            await redis.hincrby(f"{base_key}:count", f"{method}:{endpoint}", 1)
            await redis.hincrby(f"{base_key}:duration", f"{method}:{endpoint}", int(duration_ms))
            
            if status_code >= 400:
                await redis.hincrby(f"{base_key}:errors", f"{method}:{endpoint}", 1)
            
            if tenant_id:
                await redis.hincrby(f"{base_key}:tenant", tenant_id, 1)
            
            await redis.expire(f"{base_key}:count", 86400 * 30)
            await redis.expire(f"{base_key}:duration", 86400 * 30)
            await redis.expire(f"{base_key}:errors", 86400 * 30)
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    @staticmethod
    async def get_metrics(endpoint: Optional[str] = None, date: Optional[str] = None) -> dict:
        """Get aggregated metrics"""
        
        try:
            redis = await get_redis()
            date = date or datetime.now(timezone.utc).strftime('%Y-%m-%d')
            base_key = f"{MetricsCollector.METRICS_KEY_PREFIX}:{date}"
            
            counts = await redis.hgetall(f"{base_key}:count")
            durations = await redis.hgetall(f"{base_key}:duration")
            errors = await redis.hgetall(f"{base_key}:errors")
            
            results = {}
            for key in counts:
                count = int(counts.get(key, 0))
                duration = int(durations.get(key, 0))
                error_count = int(errors.get(key, 0))
                
                method, endpoint = key.split(':', 1)
                
                if endpoint == endpoint or endpoint is None:
                    results[key] = {
                        'requests': count,
                        'avg_duration_ms': duration // count if count > 0 else 0,
                        'errors': error_count,
                        'error_rate': error_count / count if count > 0 else 0,
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request timing and metrics"""
    
    EXCLUDED_PATHS = {'/health', '/health/ready', '/health/live', '/metrics', '/docs', '/openapi.json'}
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXCLUDED_PATHS or request.url.path.startswith('/docs'):
            return await call_next(request)
        
        start_time = time.perf_counter()
        
        tenant_id = getattr(request.state, 'tenant_id', None)
        user_id = getattr(request.state, 'user_id', None)
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            if status_code >= 400 or duration_ms > 1000:
                logger.warning(
                    f"Request: {request.method} {request.url.path} "
                    f"status={status_code} duration={duration_ms:.2f}ms"
                )
            
            await MetricsCollector.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                duration_ms=duration_ms,
                tenant_id=tenant_id,
            )
        
        return response


class PerformanceAlertMiddleware(BaseHTTPMiddleware):
    """Middleware to alert on slow requests"""
    
    SLOW_REQUEST_THRESHOLD_MS = 5000
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms"
            )
        
        response.headers['X-Response-Time'] = str(round(duration_ms, 2))
        
        return response


class MetricsSummaryMiddleware(BaseHTTPMiddleware):
    """Add metrics headers to responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        response.headers['X-Metrics-Enabled'] = 'true'
        response.headers['X-Pipeline-Version'] = '1.0.0'
        
        return response