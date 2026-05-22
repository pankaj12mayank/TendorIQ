"""Authentication Dependencies - FastAPI Dependency Injection"""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import AuthContext
from ...core.auth_resolver import resolve_auth_from_token
from ...core.database import get_db
from ...core.middleware import get_current_tenant_id
from ...core.rbac import RBACService, Permission

ClerkUser = dict


async def get_current_user(
    request: Request,
    authorization: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Get current authenticated user (reuse middleware auth when present)."""
    existing = getattr(request.state, 'auth', None)
    if existing:
        return existing

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing authorization header',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    if not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authorization header format',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    token = authorization.replace('Bearer ', '').strip()
    auth = await resolve_auth_from_token(token, db)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    request.state.auth = auth
    return auth


async def get_optional_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[AuthContext]:
    """Get current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(request, authorization, db)
    except HTTPException:
        return None


def get_optional_tenant_id(request: Request) -> Optional[str]:
    """Tenant id bound by TenantMiddleware (preferred) or None."""
    return get_current_tenant_id(request)


async def resolve_tenant_id(
    request: Request,
    auth: AuthContext = Depends(get_current_user),
) -> str:
    """Resolved tenant for route handlers — middleware state, then JWT."""
    tenant_id = get_current_tenant_id(request) or auth.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant context required',
        )
    return str(tenant_id)


def require_tenant_access(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    """Require user to have tenant access"""
    if not auth.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant context required',
        )
    return auth


def require_super_admin(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    """Require user to be super admin"""
    if not auth.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Super admin access required',
        )
    return auth


def check_permission(auth: AuthContext, permission: Permission | str) -> bool:
    """Check if user has specific permission (service-layer helper)."""
    role = auth.membership_role or auth.role
    return RBACService.has_permission(role, permission)


from .permissions import require_tenant_permission as require_permission

CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
OptionalUser = Annotated[Optional[AuthContext], Depends(get_optional_user)]
TenantID = Annotated[str, Depends(resolve_tenant_id)]
OptionalTenantID = Annotated[Optional[str], Depends(get_optional_tenant_id)]
SuperAdmin = Annotated[AuthContext, Depends(require_super_admin)]