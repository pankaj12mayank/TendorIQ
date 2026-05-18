"""Middleware Components - Enhanced with Auth"""

import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import get_logger
from .config import settings

logger = get_logger('middleware')


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id

        return response


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = request.headers.get('X-Tenant-ID')

        if tenant_id:
            request.state.tenant_id = tenant_id
            logger = logger.bind(tenant_id=tenant_id)

        response = await call_next(request)
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
        except Exception:
            pass

        return await call_next(request)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for JWT validation"""

    PUBLIC_PATHS = [
        '/',
        '/health',
        '/health/ready',
        '/docs',
        '/redoc',
        '/openapi.json',
        '/api/v1/auth/clerk/webhook',
        '/api/v1/webhooks/clerk',
        '/api/v1/webhooks/stripe',
        '/api/v1/webhooks/resend',
    ]

    PUBLIC_PREFIXES = [
        '/api/v1/auth/',
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if self._is_public_path(path):
            return await call_next(request)

        if path.startswith('/api/v1/webhooks'):
            return await call_next(request)

        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={
                    'success': False,
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Missing or invalid authorization header',
                    },
                },
                headers={'WWW-Authenticate': 'Bearer'},
            )

        token = auth_header.replace('Bearer ', '')

        from .auth import AuthService

        auth_service = AuthService()
        payload = auth_service.verify_token(token)

        if not payload:
            return JSONResponse(
                status_code=401,
                content={
                    'success': False,
                    'error': {
                        'code': 'TOKEN_EXPIRED',
                        'message': 'Invalid or expired token',
                    },
                },
                headers={'WWW-Authenticate': 'Bearer'},
            )

        from .auth import AuthContext

        request.state.auth = AuthContext(
            user_id=payload.sub,
            email=payload.email,
            role=payload.role,
            tenant_id=payload.tenant_id,
        )

        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        if path in self.PUBLIC_PATHS:
            return True

        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True

        return False