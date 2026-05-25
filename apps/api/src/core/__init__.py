"""Core application components (lazy — avoids importing DB engine at package import)."""

from .config import get_settings, settings

__all__ = [
    'settings',
    'get_settings',
    'Base',
    'engine',
    'async_session_maker',
    'get_db',
    'get_db_session',
]


def __getattr__(name: str):
    if name in __all__:
        from . import database

        return getattr(database, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
