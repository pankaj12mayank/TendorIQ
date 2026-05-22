"""Local JWT login helpers (no FastAPI/Clerk dependencies)."""

from datetime import datetime, timezone
from typing import Any, Optional

from .auth import AuthService, AuthContext
from .rbac import RBACService
from .roles import is_platform_super_admin, normalize_membership_role, PLATFORM_ROLE_SUPER_ADMIN


def permissions_for_role(role: str, membership_role: Optional[str]) -> list[str]:
    """Canonical permission strings (API Permission enum values) for FE + RBAC."""
    if is_platform_super_admin(role):
        perms = sorted({p.value for p in RBACService.get_role_permissions(PLATFORM_ROLE_SUPER_ADMIN)})
        if 'all' not in perms:
            perms = ['all', *perms]
        return perms
    effective = normalize_membership_role(membership_role) or normalize_membership_role(role)
    if not effective:
        return sorted({p.value for p in RBACService.get_role_permissions('viewer')})
    return sorted({p.value for p in RBACService.get_role_permissions(effective)})


def login_user_payload(
    *,
    user_id: str,
    email: str,
    name: Optional[str],
    role: str,
    membership_role: Optional[str],
    tenant_id: Optional[str],
    is_super_admin: bool,
) -> dict:
    display_role = PLATFORM_ROLE_SUPER_ADMIN if is_super_admin else role
    perms_role = PLATFORM_ROLE_SUPER_ADMIN if is_super_admin else (membership_role or role)
    return {
        'id': user_id,
        'user_id': user_id,
        'email': email,
        'name': name,
        'role': display_role,
        'membership_role': membership_role,
        'tenant_id': tenant_id,
        'is_super_admin': is_super_admin,
        'permissions': permissions_for_role(perms_role, membership_role),
    }


def issue_access_token(
    *,
    user_id: str,
    email: str,
    role: str,
    tenant_id: Optional[str] = None,
    membership_role: Optional[str] = None,
) -> str:
    """Issue access JWT via AuthService (single code path)."""
    return issue_session_tokens(
        user_id=user_id,
        email=email,
        role=role,
        tenant_id=tenant_id,
        membership_role=membership_role,
    )['access_token']


def issue_session_tokens(
    *,
    user_id: str,
    email: str,
    role: str,
    tenant_id: Optional[str] = None,
    membership_role: Optional[str] = None,
) -> dict[str, Any]:
    """Issue access + refresh tokens using AuthService (single builder)."""
    auth_service = AuthService()
    is_super = is_platform_super_admin(role)
    effective_membership = membership_role or (
        None if is_super else normalize_membership_role(role)
    )
    platform_role = PLATFORM_ROLE_SUPER_ADMIN if is_super else role
    access_token, access_exp = auth_service.create_access_token(
        user_id=user_id,
        email=email,
        role=platform_role,
        tenant_id=tenant_id,
        membership_role=effective_membership,
    )
    refresh_token, _refresh_exp = auth_service.create_refresh_token(
        user_id,
        email=email,
        role=platform_role,
        tenant_id=tenant_id,
        membership_role=effective_membership,
    )
    now = datetime.now(timezone.utc)
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': int((access_exp - now).total_seconds()),
        'token_type': 'bearer',
    }


def build_me_response(
    auth: AuthContext,
    *,
    name: Optional[str] = None,
    tenant_id: Optional[str] = None,
    is_super_admin: bool = False,
) -> dict[str, Any]:
    """Stable `/auth/me` payload aligned with login user object."""
    membership_role = auth.membership_role or normalize_membership_role(auth.role)
    display_role = (
        PLATFORM_ROLE_SUPER_ADMIN
        if is_super_admin
        else (membership_role or auth.role or 'member')
    )
    resolved_tenant = tenant_id if tenant_id is not None else auth.tenant_id
    perms = permissions_for_role(
        PLATFORM_ROLE_SUPER_ADMIN if is_super_admin else display_role,
        membership_role,
    )
    return {
        'id': auth.user_id,
        'user_id': auth.user_id,
        'email': auth.email or '',
        'name': name,
        'role': display_role,
        'membership_role': membership_role,
        'tenant_id': resolved_tenant,
        'is_super_admin': is_super_admin,
        'permissions': perms,
    }
