"""Tenant-scoped storage key helpers."""


def assert_tenant_storage_key(storage_key: str, tenant_id: str) -> None:
    """Reject path traversal and cross-tenant keys."""
    if not tenant_id:
        raise ValueError('Tenant id required')
    normalized = storage_key.replace('\\', '/').lstrip('/')
    if '..' in normalized.split('/'):
        raise ValueError('Invalid storage key')
    if not normalized.startswith(f'{tenant_id}/'):
        raise ValueError('Storage key does not belong to tenant')
