"""Role-Based Access Control (RBAC) System"""

from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request, status

from .logging import get_logger

logger = get_logger('rbac')


class UserRole(str, Enum):
    """System-level user roles"""
    SUPER_ADMIN = 'super_admin'
    TENANT_ADMIN = 'tenant_admin'
    USER = 'user'


class MembershipRole(str, Enum):
    """Tenant membership roles"""
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'
    VIEWER = 'viewer'


class Permission(str, Enum):
    """Available permissions"""

    # Tenders
    TENDER_CREATE = 'tender:create'
    TENDER_READ = 'tender:read'
    TENDER_UPDATE = 'tender:update'
    TENDER_DELETE = 'tender:delete'
    TENDER_PUBLISH = 'tender:publish'

    # Bids
    BID_CREATE = 'bid:create'
    BID_READ = 'bid:read'
    BID_UPDATE = 'bid:update'
    BID_DELETE = 'bid:delete'
    BID_ACCEPT = 'bid:accept'
    BID_REJECT = 'bid:reject'

    # Documents
    DOCUMENT_CREATE = 'document:create'
    DOCUMENT_READ = 'document:read'
    DOCUMENT_DELETE = 'document:delete'

    # Organizations/Tenants
    ORG_READ = 'org:read'
    ORG_UPDATE = 'org:update'
    ORG_DELETE = 'org:delete'
    ORG_MANAGE_MEMBERS = 'org:manage_members'

    # Users
    USER_INVITE = 'user:invite'
    USER_MANAGE = 'user:manage'

    # Settings
    SETTINGS_READ = 'settings:read'
    SETTINGS_UPDATE = 'settings:update'

    # Analytics
    ANALYTICS_VIEW = 'analytics:view'

    # AI Features
    AI_ANALYSIS = 'ai:analysis'

    # API Access
    API_ACCESS = 'api:access'


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    'super_admin': {
        Permission.TENDER_CREATE,
        Permission.TENDER_READ,
        Permission.TENDER_UPDATE,
        Permission.TENDER_DELETE,
        Permission.TENDER_PUBLISH,
        Permission.BID_CREATE,
        Permission.BID_READ,
        Permission.BID_UPDATE,
        Permission.BID_DELETE,
        Permission.BID_ACCEPT,
        Permission.BID_REJECT,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_DELETE,
        Permission.ORG_READ,
        Permission.ORG_UPDATE,
        Permission.ORG_DELETE,
        Permission.ORG_MANAGE_MEMBERS,
        Permission.USER_INVITE,
        Permission.USER_MANAGE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_UPDATE,
        Permission.ANALYTICS_VIEW,
        Permission.AI_ANALYSIS,
        Permission.API_ACCESS,
    },
    'owner': {
        Permission.TENDER_CREATE,
        Permission.TENDER_READ,
        Permission.TENDER_UPDATE,
        Permission.TENDER_DELETE,
        Permission.TENDER_PUBLISH,
        Permission.BID_CREATE,
        Permission.BID_READ,
        Permission.BID_UPDATE,
        Permission.BID_DELETE,
        Permission.BID_ACCEPT,
        Permission.BID_REJECT,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_DELETE,
        Permission.ORG_READ,
        Permission.ORG_UPDATE,
        Permission.ORG_DELETE,
        Permission.ORG_MANAGE_MEMBERS,
        Permission.USER_INVITE,
        Permission.USER_MANAGE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_UPDATE,
        Permission.ANALYTICS_VIEW,
        Permission.AI_ANALYSIS,
        Permission.API_ACCESS,
    },
    'admin': {
        Permission.TENDER_CREATE,
        Permission.TENDER_READ,
        Permission.TENDER_UPDATE,
        Permission.TENDER_DELETE,
        Permission.TENDER_PUBLISH,
        Permission.BID_CREATE,
        Permission.BID_READ,
        Permission.BID_UPDATE,
        Permission.BID_DELETE,
        Permission.BID_ACCEPT,
        Permission.BID_REJECT,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_DELETE,
        Permission.ORG_READ,
        Permission.ORG_UPDATE,
        Permission.ORG_MANAGE_MEMBERS,
        Permission.USER_INVITE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_UPDATE,
        Permission.ANALYTICS_VIEW,
        Permission.AI_ANALYSIS,
        Permission.API_ACCESS,
    },
    'member': {
        Permission.TENDER_CREATE,
        Permission.TENDER_READ,
        Permission.TENDER_UPDATE,
        Permission.BID_CREATE,
        Permission.BID_READ,
        Permission.BID_UPDATE,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.ORG_READ,
        Permission.SETTINGS_READ,
        Permission.ANALYTICS_VIEW,
        Permission.AI_ANALYSIS,
    },
    'viewer': {
        Permission.TENDER_READ,
        Permission.BID_READ,
        Permission.DOCUMENT_READ,
        Permission.ORG_READ,
        Permission.SETTINGS_READ,
    },
}


class RBACService:
    """RBAC service for permission checking"""

    @staticmethod
    def get_role_permissions(role: str) -> set[Permission]:
        """Get permissions for a role"""
        return ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def has_permission(role: str, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in RBACService.get_role_permissions(role)

    @staticmethod
    def has_any_permission(role: str, permissions: list[Permission]) -> bool:
        """Check if role has any of the specified permissions"""
        role_perms = RBACService.get_role_permissions(role)
        return any(p in role_perms for p in permissions)

    @staticmethod
    def has_all_permissions(role: str, permissions: list[Permission]) -> bool:
        """Check if role has all of the specified permissions"""
        role_perms = RBACService.get_role_permissions(role)
        return all(p in role_perms for p in permissions)


def require_permission(permission: Permission):
    """Decorator to require specific permission"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            auth_context = getattr(request.state, 'auth', None)

            if not auth_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Authentication required',
                )

            role = auth_context.membership_role or auth_context.role
            if not RBACService.has_permission(role, permission):
                logger.warning(
                    f'Permission denied: {permission.value} for role {role}',
                    user_id=auth_context.user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f'Permission denied: {permission.value}',
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(permissions: list[Permission]):
    """Decorator to require any of the specified permissions"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            auth_context = getattr(request.state, 'auth', None)

            if not auth_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Authentication required',
                )

            role = auth_context.membership_role or auth_context.role
            if not RBACService.has_any_permission(role, permissions):
                logger.warning(
                    f'Permission denied for role {role}',
                    user_id=auth_context.user_id,
                    required=permissions,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Permission denied',
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(allowed_roles: list[str]):
    """Decorator to require specific role"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            auth_context = getattr(request.state, 'auth', None)

            if not auth_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Authentication required',
                )

            membership_role = auth_context.membership_role
            user_role = auth_context.role

            if membership_role not in allowed_roles and user_role not in allowed_roles:
                logger.warning(
                    f'Role denied for user {auth_context.user_id}',
                    required_roles=allowed_roles,
                    user_role=user_role,
                    membership_role=membership_role,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Role not permitted',
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


rbac_service = RBACService()