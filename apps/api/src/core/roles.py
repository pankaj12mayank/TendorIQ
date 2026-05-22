"""Canonical role definitions — platform vs tenant membership.

Platform roles (JWT `role`, never stored on ``users.role``):
  - super_admin: env-backed platform operator

Tenant roles (JWT ``membership_role`` + ``memberships.role``):
  - owner, admin, manager, analyst, member, viewer

UI alias ``tenant_admin`` maps to RBAC ``admin`` (not a DB value).
"""

from typing import Optional

PLATFORM_ROLE_SUPER_ADMIN = 'super_admin'

MEMBERSHIP_ROLES = frozenset({
    'owner',
    'admin',
    'manager',
    'analyst',
    'member',
    'viewer',
})

# Legacy / UI alias — not persisted in memberships CHECK
ROLE_ALIASES = {
    'tenant_admin': 'admin',
    'user': 'member',
}


def normalize_membership_role(role: Optional[str]) -> Optional[str]:
    """Map aliases to a valid membership role for RBAC and DB."""
    if not role:
        return None
    r = role.strip().lower()
    if r == PLATFORM_ROLE_SUPER_ADMIN:
        return None
    if r in MEMBERSHIP_ROLES:
        return r
    return ROLE_ALIASES.get(r)


def is_platform_super_admin(role: Optional[str]) -> bool:
    return (role or '').strip().lower() == PLATFORM_ROLE_SUPER_ADMIN


def coerce_membership_role(role: str, default: str = 'member') -> str:
    """Return a value safe for ``memberships.role`` CHECK constraint."""
    normalized = normalize_membership_role(role)
    if normalized and normalized in MEMBERSHIP_ROLES:
        return normalized
    if role in MEMBERSHIP_ROLES:
        return role
    return default
