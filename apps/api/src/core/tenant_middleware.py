"""Re-export shim — consolidated into middleware.py.

All classes/functions have been moved to core.middleware.
This module kept for backward compatibility during transition.
"""

from .middleware import (
    TenantMiddleware,
    TenantContext,
    TenantIsolationMiddleware,
    TenantRateLimitMiddleware,
    get_tenant_context,
    get_current_tenant_id,
)

__all__ = [
    'TenantMiddleware',
    'TenantContext',
    'TenantIsolationMiddleware',
    'TenantRateLimitMiddleware',
    'get_tenant_context',
    'get_current_tenant_id',
]
