"""Permission enforcement — FastAPI dependencies (tenant-aware)."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.rbac import Permission, RBACService
from ...core.auth import AuthContext
from .auth import get_current_user
from .tenant import verify_tenant_access
from .audit import audit_logger


class TenantPermissionChecker:
    """Tenant-aware permission checking using membership role."""

    @staticmethod
    def has_tenant_permission(auth: AuthContext, permission: Permission | str) -> bool:
        role = auth.membership_role or auth.role
        return RBACService.has_permission(role, permission)

    @staticmethod
    def has_any_tenant_permission(
        auth: AuthContext,
        permissions: list[Permission],
    ) -> bool:
        role = auth.membership_role or auth.role
        return RBACService.has_any_permission(role, permissions)

    @staticmethod
    def has_all_tenant_permissions(
        auth: AuthContext,
        permissions: list[Permission],
    ) -> bool:
        role = auth.membership_role or auth.role
        return RBACService.has_all_permissions(role, permissions)


def require_tenant_permission(permission: Permission):
    """Dependency: authenticated tenant member with a specific permission."""

    async def permission_checker(
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        if auth.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Platform super_admin must use /api/v1/admin/platform routes',
            )
        if not auth.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Tenant context required',
            )
        if not TenantPermissionChecker.has_tenant_permission(auth, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Permission denied: {permission.value}',
            )
        return auth

    return permission_checker


def require_tenant_any_permission(permissions: list[Permission]):
    """Dependency: require any of the listed permissions."""

    async def permission_checker(
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        if auth.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Platform super_admin must use /api/v1/admin/platform routes',
            )
        if not auth.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Tenant context required',
            )
        if not TenantPermissionChecker.has_any_tenant_permission(auth, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Permission denied',
            )
        return auth

    return permission_checker


def require_tenant_all_permissions(permissions: list[Permission]):
    """Dependency: require all listed permissions."""

    async def permission_checker(
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        if auth.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Platform super_admin must use /api/v1/admin/platform routes',
            )
        if not auth.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Tenant context required',
            )
        if not TenantPermissionChecker.has_all_tenant_permissions(auth, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Permission denied',
            )
        return auth

    return permission_checker


def require_tenant_role(allowed_roles: list[str]):
    """Dependency: require specific tenant membership role."""

    async def role_checker(
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        if auth.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Platform super_admin must use /api/v1/admin/platform routes',
            )
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
    """Check tenant access and permission (for service-layer calls)."""
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
    """Service-layer helpers with audit logging."""

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
