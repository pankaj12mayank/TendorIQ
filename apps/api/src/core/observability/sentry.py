"""Sentry Integration for Error Tracking and Performance Monitoring"""

import logging
from functools import wraps
from typing import Any, Callable, Optional

from sentry_sdk import (
    init,
    capture_message,
    capture_exception,
    set_extra,
    set_tag,
    add_breadcrumb,
    Hub,
    Transaction,
    Span,
)
from sentry_sdk.integrations.fastapi import FastAPIIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from ..config import settings

logger = logging.getLogger(__name__)


class SentryConfig:
    TRACES_SAMPLE_RATE = 0.1
    PROFILES_SAMPLE_RATE = 0.1
    
    @classmethod
    def should_enable(cls) -> bool:
        return bool(settings.SENTRY_DSN)


class SentryService:
    _initialized = False
    
    @classmethod
    def initialize(cls) -> None:
        if cls._initialized or not SentryConfig.should_enable():
            return
        
        init(
            dsn=settings.SENTRY_DSN,
            environment=settings.NODE_ENV,
            release=f'tendoriq@{settings.VERSION}' if hasattr(settings, 'VERSION') else '1.0.0',
            traces_sample_rate=SentryConfig.TRACES_SAMPLE_RATE,
            profiles_sample_rate=SentryConfig.PROFILES_SAMPLE_RATE,
            integrations=[
                FastAPIIntegration(),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
            attach_stacktrace=True,
            include_extras=True,
            max_breadcrumbs=100,
            before_send=lambda event, hint: cls._filter_event(event, hint),
        )
        
        cls._initialized = True
        logger.info('Sentry initialized')
    
    @staticmethod
    def _filter_event(event: dict, hint: dict) -> Optional[dict]:
        """Filter out noisy events"""
        
        if hint.get('exc_info'):
            exc_type = hint['exc_info'][0]
            if exc_type.__name__ in ['ValidationError', 'HTTPException']:
                return None
        
        return event
    
    @classmethod
    def capture_message(cls, message: str, level: str = 'info', **tags: Any) -> None:
        """Capture a custom message"""
        if not cls._initialized:
            return
        
        set_extra(**tags)
        capture_message(message, level=level)
    
    @classmethod
    def capture_exception(cls, error: Exception, context: dict = None) -> None:
        """Capture an exception with context"""
        if not cls._initialized:
            return
        
        if context:
            set_extra('context', context)
        
        capture_exception(error)
    
    @classmethod
    def set_user(cls, user_id: str, email: str = None, ip_address: str = None) -> None:
        """Set user context"""
        from sentry_sdk import set_user as sentry_set_user
        
        sentry_set_user({
            'id': user_id,
            'email': email,
            'ip_address': ip_address,
        })
    
    @classmethod
    def add_breadcrumb(cls, category: str, message: str, level: str = 'info', **data: Any) -> None:
        """Add a breadcrumb for tracing"""
        add_breadcrumb(
            category=category,
            message=message,
            level=level,
            data=data,
        )
    
    @classmethod
    def start_transaction(cls, name: str, op: str = 'custom') -> Transaction:
        """Start a custom transaction"""
        return Transaction(op=op, name=name)
    
    @classmethod
    def trace(cls, name: str, op: str = 'custom'):
        """Decorator to trace function execution"""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with cls.start_transaction(f'{func.__module__}.{func.__name__}', op):
                    return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with cls.start_transaction(f'{func.__module__}.{func.__name__}', op):
                    return func(*args, **kwargs)
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator


def init_sentry():
    """Initialize Sentry on application startup"""
    SentryService.initialize()


def sentry_middleware(request, call_next):
    """FastAPI middleware for Sentry performance monitoring"""
    
    if not SentryService._initialized:
        return call_next(request)
    
    transaction = Hub.current.start_transaction(
        name=f'{request.method} {request.url.path}',
        op='http.server',
    )
    
    try:
        response = call_next(request)
        
        set_tag('http.status_code', response.status_code)
        transaction.status = 'ok' if response.status_code < 400 else 'error'
        
        return response
    except Exception as e:
        transaction.status = 'internal_error'
        SentryService.capture_exception(e, {'path': str(request.url)})
        raise
    finally:
        transaction.finish()


class ErrorTracker:
    """Track specific error patterns"""
    
    @staticmethod
    def track_validation_error(field: str, error: str) -> None:
        set_tag('validation.field', field)
        capture_message(f'Validation error: {error}', level='warning')
    
    @staticmethod
    def track_rate_limit(endpoint: str, user_id: str) -> None:
        set_tag('rate_limit.endpoint', endpoint)
        set_tag('rate_limit.user', user_id)
        capture_message('Rate limit exceeded', level='warning')
    
    @staticmethod
    def track_auth_failure(email: str, reason: str) -> None:
        set_tag('auth.email', email)
        set_tag('auth.reason', reason)
        capture_message('Authentication failed', level='warning')
    
    @staticmethod
    def track_queue_failure(queue: str, job_id: str, error: str) -> None:
        set_tag('queue.name', queue)
        set_tag('queue.job_id', job_id)
        SentryService.capture_exception(Exception(error), {'queue': queue})
    
    @staticmethod
    def track_ai_error(provider: str, model: str, error: str) -> None:
        set_tag('ai.provider', provider)
        set_tag('ai.model', model)
        capture_message(f'AI error: {error}', level='error')