"""Observability Module - Monitoring, Metrics, Health Checks"""

__all__ = [
    'SentryService',
    'SentryConfig',
    'init_sentry',
    'sentry_middleware',
    'ErrorTracker',
]


def __getattr__(name: str):
    if name in __all__:
        from . import sentry as _sentry

        return getattr(_sentry, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')