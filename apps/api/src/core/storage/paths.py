"""Re-exports path helpers; startup hook uses settings."""

from pathlib import Path

from ..local_storage_paths import api_app_root, resolve_storage_local_path

__all__ = ['api_app_root', 'resolve_storage_local_path', 'ensure_local_storage_root']


def ensure_local_storage_root() -> Path:
    from ..config import settings

    root = settings.resolved_storage_local_path
    if settings.STORAGE_PROVIDER == 'local':
        root.mkdir(parents=True, exist_ok=True)
    return root
