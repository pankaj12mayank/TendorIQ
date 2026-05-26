"""Tenant / user scoped storage key helpers."""

from typing import Optional


def assert_tenant_storage_key(
    storage_key: str,
    tenant_id: str,
    owner_id: Optional[str] = None,
) -> None:
    """Reject path traversal and keys outside tenant or user scope."""
    if not tenant_id and not owner_id:
        raise ValueError('Tenant or owner id required')
    normalized = storage_key.replace('\\', '/').lstrip('/')
    if '..' in normalized.split('/'):
        raise ValueError('Invalid storage key')
    prefixes: list[str] = []
    if tenant_id:
        prefixes.append(f'{tenant_id}/')
    if owner_id:
        prefixes.append(f'users/{owner_id}/')
    if prefixes and not any(normalized.startswith(p) for p in prefixes):
        raise ValueError('Storage key does not belong to this workspace')
