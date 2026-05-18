"""Permission Enforcement - Tenant-Aware Permission Checks"""

from typing import Callable, Optional
from functools import wraps
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.rbac import Permission, RBACService
from ...core.auth import AuthContext
from .auth import get_current_user
from .tenant import get_tenant_context, verify_tenant_access
from .audit import audit_logger


class TenantPermissionChecker:
    """Tenant-aware permission checking"""

    @staticmethod
    def has_tenant_permission(
        auth: AuthContext,
        permission: Permission,
    ) -> bool:
        """Check if user has permission in their tenant context"""
        role = auth.membership_role or auth.role
        return RBACService.has_permission(role, permission)

    @staticmethod
    def has_any_tenant_permission(
        auth: AuthContext,
        permissions: list[Permission],
    ) -> bool:
        """Check if user has any of the specified permissions"""
        role = auth.membership_role or auth.role
        return RBACService.has_any_permission(role, permissions)

    @staticmethod
    def has_all_tenant_permissions(
        auth: AuthContext,
        permissions: list[Permission],
    ) -> bool:
        """Check if user has all of the specified permissions"""
        role = auth.membership_role or auth.role
        return RBACService.has_all_permissions(role, permissions)


def require_tenant_permission(permission: Permission):
    """Dependency to require specific permission in tenant context"""

    async def permission_checker(
        auth: AuthContext = Depends(get_current_user),
        request: Request = None,
    ) -> AuthContext:
        if not TenantPermissionChecker.has_tenant_permission(auth, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Permission denied: {permission.value}',
            )
        return auth

    return permission_checker


def require_tenant_any_permission(permissions: list[Permission]):
    """Dependency to require any of the specified permissions"""

    async def permission_checker(
        auth: AuthContext = Depends(get_current_user),
        request: Request = None,
    ) -> AuthContext:
        if not TenantPermissionChecker.has_any_tenant_permission(auth, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Permission denied',
            )
        return auth

    return permission_checker


def require_tenant_all_permissions(permissions: list[Permission]):
    """Dependency to require all of the specified permissions"""

    async def permission_checker(
        auth: AuthContext = Depends(get_current_user),
        request: Request = None,
    ) -> AuthContext:
        if not TenantPermissionChecker.has_all_tenant_permissions(auth, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Permission denied',
            )
        return auth

    return permission_checker


def require_tenant_role(allowed_roles: list[str]):
    """Dependency to require specific tenant role"""

    async def role_checker(
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        role = auth.membership_role or auth.role
        
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Role not permitted. Required: {allowed_roles}',
            )
        return auth

    return role_checker


async def check_tenant_and_permission(
    db: AsyncSession,
    auth: AuthContext,
    tenant_id: str,
    permission: Permission,
    request: Optional[Request] = None,
) -> bool:
    """Check both tenant access and permission"""
    valid, error = await verify_tenant_access(db, auth.user_id, tenant_id)
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    if not TenantPermissionChecker.has_tenant_permission(auth, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Permission denied: {permission.value}',
        )

    return True


class ProtectedTenantEndpoint:
    """Mixin for protected tenant endpoints with audit logging"""

    @staticmethod
    async def require_create(
        db: AsyncSession,
        auth: AuthContext,
        tenant_id: str,
        resource_type: str,
        request: Optional[Request] = None,
    ):
        await check_tenant_and_permission(
            db, auth, tenant_id, Permission.TENDER_CREATE, request
        )
        
        await audit_logger.log_action(
            db,
            UUID(tenant_id),
            UUID(auth.user_id),
            action='create_attempt',
            resource_type=resource_type,
            request=request,
        )

    @staticmethod
    async def require_read(
        db: AsyncSession,
        auth: AuthContext,
        tenant_id: str,
        resource_type: str,
        request: Optional[Request] = None,
    ):
        await check_tenant_and_permission(
            db, auth, tenant_id, Permission.TENDER_READ, request
        )

    @staticmethod
    async def require_update(
        db: AsyncSession,
        auth: AuthContext,
        tenant_id: str,
        resource_type: str,
        request: Optional[Request] = None,
    ):
        await check_tenant_and_permission(
            db, auth, tenant_id, Permission.TENDER_UPDATE, request
        )

    @staticmethod
    async def require_delete(
        db: AsyncSession,
        auth: AuthContext,
        tenant_id: str,
        resource_type: str,
        request: Optional[Request] = None,
    ):
        await check_tenant_and_permission(
            db, auth, tenant_id, Permission.TENDER_DELETE, request
        )


perm_checker = TenantPermissionChecker()
protected_endpoint = ProtectedTenantEndpoint()