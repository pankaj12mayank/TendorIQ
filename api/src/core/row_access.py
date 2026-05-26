"""Row-level access for tenant-scoped resources (beyond RBAC permission strings)."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from .roles import normalize_membership_role

# Roles that may modify any resource within their tenant.
_TENANT_MANAGER_ROLES = frozenset({'owner', 'admin', 'manager'})


def effective_membership_role(
    membership_role: Optional[str],
    platform_role: Optional[str] = None,
) -> str:
    return (
        normalize_membership_role(membership_role)
        or normalize_membership_role(platform_role)
        or 'member'
    )


def can_modify_tenant_resource(
    *,
    user_id: str,
    membership_role: Optional[str],
    created_by_id: Any,
    platform_role: Optional[str] = None,
) -> bool:
    """
    Return True when the user may update/delete a tenant row they do not own.

    Managers and above may change any tenant resource; other roles may only
    change rows they created (``created_by_id``).
    """
    role = effective_membership_role(membership_role, platform_role)
    if role in _TENANT_MANAGER_ROLES:
        return True
    if created_by_id is None:
        return False
    return str(created_by_id) == str(user_id)


def resource_owner_id_from_metadata(metadata: Optional[dict]) -> Optional[str]:
    if not metadata:
        return None
    for key in ('uploaded_by_id', 'created_by_id', 'owner_id'):
        value = metadata.get(key)
        if value:
            return str(value)
    return None
