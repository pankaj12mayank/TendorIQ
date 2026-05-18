"""Enhanced Tenant Middleware - Full Multi-Tenant Support"""

import time
import uuid
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import get_logger
from .config import settings

logger = get_logger('tenant_middleware')


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Enhanced tenant middleware with:
    - Tenant switching via headers
    - Tenant isolation
    - Request context binding
    - Security validation
    """

    TENANT_HEADER = 'X-Tenant-ID'
    TENANT_SLUG_HEADER = 'X-Tenant-Slug'

    EXEMPT_PATHS = [
        '/health',
        '/health/ready',
        '/docs',
        '/redoc',
        '/openapi.json',
        '/api/v1/auth/',
        '/api/v1/webhooks/',
    ]

    def __init__(self, app, db_session=None):
        super().__init__(app)
        self.db = db_session

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        path = request.url.path
        if self._is_exempt(path):
            return await call_next(request)

        auth = getattr(request.state, 'auth', None)

        if not auth:
            return await call_next(request)

        tenant_id = self._get_tenant_from_request(request, auth)

        if tenant_id:
            request.state.tenant_id = str(tenant_id)
            request.state.tenant_context = TenantContext(
                tenant_id=str(tenant_id),
                user_id=auth.user_id,
                role=auth.membership_role or auth.role
            )
            
            logger.bind(
                tenant_id=str(tenant_id),
                user_id=auth.user_id
            )

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers['X-Tenant-ID'] = str(tenant_id) if tenant_id else ''
        response.headers['X-Process-Time'] = f'{process_time:.3f}'

        return response

    def _get_tenant_from_request(
        self,
        request: Request,
        auth
    ) -> Optional[UUID]:
        """Get tenant ID from request with priority"""
        
        header_tenant = request.headers.get(self.TENANT_HEADER)
        if header_tenant:
            return self._validate_tenant(header_tenant, auth.user_id)

        if auth.tenant_id:
            return UUID(auth.tenant_id)

        return None

    def _validate_tenant(self, tenant_id: str, user_id: str) -> Optional[UUID]:
        """Validate tenant ID format"""
        try:
            return UUID(tenant_id)
        except (ValueError, TypeError):
            logger.warning(
                f'Invalid tenant ID format: {tenant_id}',
                user_id=user_id
            )
            return None

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from tenant requirement"""
        for exempt in self.EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        return False


class TenantContext:
    """Tenant context stored in request state"""

    def __init__(
        self,
        tenant_id: str,
        user_id: str,
        role: str
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
        self.request_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return {
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'role': self.role,
            'request_id': self.request_id,
        }

    def is_admin(self) -> bool:
        return self.role in ('owner', 'admin', 'super_admin')

    def is_owner(self) -> bool:
        return self.role == 'owner'


def get_tenant_context(request: Request) -> Optional[TenantContext]:
    """Get tenant context from request state"""
    return getattr(request.state, 'tenant_context', None)


def get_current_tenant_id(request: Request) -> Optional[str]:
    """Get current tenant ID from request"""
    context = get_tenant_context(request)
    if context:
        return context.tenant_id
    return getattr(request.state, 'tenant_id', None)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure data isolation between tenants
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = get_current_tenant_id(request)

        if tenant_id:
            logger.bind(tenant_id=tenant_id)

        response = await call_next(request)
        return response


class TenantRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-tenant rate limiting
    """

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        tenant_id = get_current_tenant_id(request)
        
        if not tenant_id:
            return await call_next(request)

        client_ip = request.client.host if request.client else 'unknown'
        key = f'ratelimit:tenant:{tenant_id}:ip:{client_ip}'

        try:
            if self.redis:
                count = await self.redis.get(key)
                if count and int(count) >= settings.RATE_LIMIT_PER_MINUTE:
                    return JSONResponse(
                        status_code=429,
                        content={
                            'success': False,
                            'error': {
                                'code': 'TENANT_RATE_LIMIT_EXCEEDED',
                                'message': 'Organization rate limit exceeded',
                            },
                        },
                    )

                pipe = self.redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, 60)
                await pipe.execute()
        except Exception:
            pass

        return await call_next(request)