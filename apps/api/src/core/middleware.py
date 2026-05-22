"""Middleware Components - Enhanced with Auth & Multi-Tenant Support"""

import time
import uuid
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .auth_resolver import resolve_auth_from_token
from .logging import get_logger
from .config import settings
from .roles import is_platform_super_admin
from .tenant_context import TenantQueryHelper as tenant_query
from .tenant_paths import is_auth_public_path, is_tenant_exempt_path, is_tenant_scoped_path

logger = get_logger('middleware')

_rate_limit_redis_warned = False


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers['X-Process-Time'] = str(process_time)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client
        global _rate_limit_redis_warned
        if settings.RATE_LIMIT_ENABLED and not self.redis and not _rate_limit_redis_warned:
            logger.warning('Rate limiting enabled but Redis is not configured; limits are inactive')
            _rate_limit_redis_warned = True

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_ip = request.client.host if request.client else 'unknown'
        key = f'ratelimit:{client_ip}:{request.url.path}'

        try:
            if self.redis:
                count = await self.redis.get(key)
                if count and int(count) >= settings.RATE_LIMIT_PER_MINUTE:
                    return JSONResponse(
                        status_code=429,
                        content={
                            'success': False,
                            'error': {
                                'code': 'RATE_LIMIT_EXCEEDED',
                                'message': 'Too many requests. Please try again later.',
                            },
                        },
                    )

                pipe = self.redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, 60)
                await pipe.execute()
        except Exception as exc:
            logger.debug('Rate limit skipped: %s', exc)

        return await call_next(request)


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

    def __init__(self, app, db_session=None):
        super().__init__(app)
        self.db = db_session

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        path = request.url.path

        if is_tenant_exempt_path(path):
            return await call_next(request)

        auth = getattr(request.state, 'auth', None)
        if not auth:
            return await call_next(request)

        if is_platform_super_admin(auth.role):
            return await call_next(request)

        tenant_id = await self._resolve_tenant_id(request, auth)
        if not tenant_id and is_tenant_scoped_path(path):
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': {
                        'code': 'TENANT_REQUIRED',
                        'message': 'Tenant ID required (JWT tenant_id or X-Tenant-ID header)',
                    },
                },
            )

        if tenant_id:
            request.state.tenant_id = tenant_id
            request.state.tenant_context = TenantContext(
                tenant_id=tenant_id,
                user_id=auth.user_id,
                role=auth.membership_role or auth.role or 'member',
            )

        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        if tenant_id:
            response.headers['X-Tenant-ID'] = tenant_id
        response.headers['X-Process-Time'] = f'{process_time:.3f}'
        return response

    async def _resolve_tenant_id(self, request: Request, auth) -> Optional[str]:
        """JWT tenant_id by default; X-Tenant-ID when membership allows."""
        header_tenant = (request.headers.get(self.TENANT_HEADER) or '').strip()
        if header_tenant:
            try:
                header_uuid = UUID(header_tenant)
            except (ValueError, TypeError):
                logger.warning('Invalid X-Tenant-ID format: %s', header_tenant)
                return None
            if auth.tenant_id and str(auth.tenant_id) == str(header_uuid):
                return str(header_uuid)
            from .database import async_session_maker

            try:
                user_uuid = UUID(str(auth.user_id))
            except (ValueError, TypeError):
                return None
            async with async_session_maker() as db:
                valid, _ = await tenant_query.verify_tenant_access(
                    db, user_uuid, header_uuid
                )
            if valid:
                return str(header_uuid)
            logger.warning(
                'X-Tenant-ID rejected for user',
                user_id=auth.user_id,
                tenant_id=header_tenant,
            )
            return None

        if auth.tenant_id:
            return str(auth.tenant_id)
        return None


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure data isolation between tenants"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = get_current_tenant_id(request)

        if tenant_id:
            logger.bind(tenant_id=tenant_id)

        response = await call_next(request)
        return response


class TenantRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-tenant rate limiting"""

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


class AuthMiddleware(BaseHTTPMiddleware):
    """Populate request.state.auth before tenant middleware and route handlers."""

    SKIP_PREFIXES = (
        '/health',
        '/docs',
        '/redoc',
        '/openapi.json',
        '/api/v1/webhooks/',
    )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if path == '/' or any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return await call_next(request)

        if is_auth_public_path(path):
            return await call_next(request)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return await call_next(request)

        token = auth_header.replace('Bearer ', '').strip()
        from .database import async_session_maker

        async with async_session_maker() as db:
            auth = await resolve_auth_from_token(token, db)

        if auth:
            request.state.auth = auth

        return await call_next(request)


class TenantContext:
    """Tenant context stored in request state"""

    def __init__(self, tenant_id: str, user_id: str, role: str):
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
