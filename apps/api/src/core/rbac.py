"""Role-Based Access Control (RBAC) System"""

from enum import Enum

from .logging import get_logger
from .roles import normalize_membership_role, PLATFORM_ROLE_SUPER_ADMIN

logger = get_logger('rbac')


class UserRole(str, Enum):
    """Platform-level roles (JWT ``role`` only — not stored on ``users.role``)."""
    SUPER_ADMIN = PLATFORM_ROLE_SUPER_ADMIN
    USER = 'user'


class MembershipRole(str, Enum):
    """Tenant membership roles"""
    OWNER = 'owner'
    ADMIN = 'admin'
    MANAGER = 'manager'
    ANALYST = 'analyst'
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


from .rbac_matrix import coerce_permission_value, load_role_permissions_matrix

ROLE_PERMISSIONS: dict[str, set[Permission]] = load_role_permissions_matrix(Permission)


class RBACService:
    """RBAC service for permission checking"""

    @staticmethod
    def get_role_permissions(role: str) -> set[Permission]:
        """Get permissions for a role"""
        if role == PLATFORM_ROLE_SUPER_ADMIN:
            return ROLE_PERMISSIONS.get('super_admin', set())
        normalized = normalize_membership_role(role) or role
        return ROLE_PERMISSIONS.get(normalized, set())

    @staticmethod
    def has_permission(role: str, permission: Permission | str) -> bool:
        """Check if role has specific permission (supports legacy alias strings)."""
        resolved = coerce_permission_value(Permission, permission)
        if resolved is None:
            return False
        return resolved in RBACService.get_role_permissions(role)

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


# Route-level enforcement: use FastAPI Depends via
# api.dependencies.permissions.require_tenant_permission
# or Annotated types in api.dependencies.rbac_deps (Layer 4).


rbac_service = RBACService()