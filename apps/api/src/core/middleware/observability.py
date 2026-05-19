"""Request timing middleware (metrics stored in logs only)."""

import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class MetricsCollector:
    @staticmethod
    async def record_request(
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        tenant_id: Optional[str] = None,
    ) -> None:
        logger.debug(
            'api_metric method=%s path=%s status=%s duration_ms=%.1f tenant=%s',
            method,
            endpoint,
            status_code,
            duration_ms,
            tenant_id,
        )


class RequestTimingMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {'/health', '/health/ready', '/health/live', '/metrics', '/docs', '/openapi.json'}

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        tenant_id = getattr(request.state, 'tenant_id', None)
        await MetricsCollector.record_request(
            request.url.path,
            request.method,
            response.status_code,
            duration_ms,
            str(tenant_id) if tenant_id else None,
        )
        return response
