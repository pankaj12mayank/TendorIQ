"""Authentication Dependencies - FastAPI Dependency Injection"""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from ...core.auth import AuthService, AuthContext, ClerkAuthService
from ...core.config import settings
from ...core.rbac import RBACService, Permission

ClerkUser = dict


async def get_current_user(authorization: Annotated[Optional[str], Header()] = None) -> AuthContext:
    """Get current authenticated user from JWT token or Clerk"""
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

    token = authorization.replace('Bearer ', '')

    # Try Clerk first if configured
    if settings.CLERK_SECRET_KEY and settings.AUTH_PROVIDER == 'clerk':
        clerk_user = await ClerkAuthService.verify_token(token)
        if clerk_user:
            return AuthContext(
                user_id=clerk_user.get('id', ''),
                email=clerk_user.get('email_addresses', [{}])[0].get('email_address'),
                role=clerk_user.get('public_metadata', {}).get('role', 'user'),
            )

    # Fall back to JWT verification
    auth_service = AuthService()
    token_payload = auth_service.verify_token(token)

    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return AuthContext(
        user_id=token_payload.sub,
        email=token_payload.email,
        role=token_payload.role,
        tenant_id=token_payload.tenant_id,
    )


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[AuthContext]:
    """Get current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def get_tenant_id(request: Request) -> Optional[str]:
    """Get tenant ID from request state or header"""
    return getattr(request.state, 'tenant_id', None)


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
    if auth.role != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Super admin access required',
        )
    return auth


def check_permission(auth: AuthContext, permission: Permission) -> bool:
    """Check if user has specific permission"""
    role = auth.membership_role or auth.role
    return RBACService.has_permission(role, permission)


def require_permission(permission: Permission):
    """Dependency for requiring specific permission"""

    def permission_checker(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        role = auth.membership_role or auth.role
        if not RBACService.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Permission denied: {permission.value}',
            )
        return auth

    return permission_checker


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
OptionalUser = Annotated[Optional[AuthContext], Depends(get_optional_user)]
TenantID = Annotated[Optional[str], Depends(get_tenant_id)]
SuperAdmin = Annotated[AuthContext, Depends(require_super_admin)]