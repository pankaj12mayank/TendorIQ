"""FastAPI dependencies for RBAC enforcement (Layer 4)."""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from ...core.auth import AuthContext
from ...core.tenant_types import parse_tenant_uuid
from ...core.rbac import Permission
from .auth import get_current_user
from .permissions import require_tenant_permission

# Re-export factory for route-level Depends(...)
RequirePermission = require_tenant_permission


async def require_tenant_member(
    auth: AuthContext = Depends(get_current_user),
) -> AuthContext:
    """Authenticated tenant user with tenant_id (blocks platform super_admin on tenant APIs)."""
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
    try:
        parse_tenant_uuid(auth.tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid tenant context',
        )
    return auth


TenantMember = Annotated[AuthContext, Depends(require_tenant_member)]

RequireTenderRead = Annotated[AuthContext, Depends(require_tenant_permission(Permission.TENDER_READ))]
RequireTenderCreate = Annotated[AuthContext, Depends(require_tenant_permission(Permission.TENDER_CREATE))]
RequireTenderUpdate = Annotated[AuthContext, Depends(require_tenant_permission(Permission.TENDER_UPDATE))]
RequireTenderDelete = Annotated[AuthContext, Depends(require_tenant_permission(Permission.TENDER_DELETE))]

RequireDocumentRead = Annotated[AuthContext, Depends(require_tenant_permission(Permission.DOCUMENT_READ))]
RequireDocumentCreate = Annotated[AuthContext, Depends(require_tenant_permission(Permission.DOCUMENT_CREATE))]
RequireDocumentDelete = Annotated[AuthContext, Depends(require_tenant_permission(Permission.DOCUMENT_DELETE))]

RequireBidRead = Annotated[AuthContext, Depends(require_tenant_permission(Permission.BID_READ))]
RequireBidCreate = Annotated[AuthContext, Depends(require_tenant_permission(Permission.BID_CREATE))]
RequireBidUpdate = Annotated[AuthContext, Depends(require_tenant_permission(Permission.BID_UPDATE))]

RequireOrgRead = Annotated[AuthContext, Depends(require_tenant_permission(Permission.ORG_READ))]
RequireOrgUpdate = Annotated[AuthContext, Depends(require_tenant_permission(Permission.ORG_UPDATE))]
RequireOrgManageMembers = Annotated[
    AuthContext, Depends(require_tenant_permission(Permission.ORG_MANAGE_MEMBERS))
]

RequireSettingsRead = Annotated[AuthContext, Depends(require_tenant_permission(Permission.SETTINGS_READ))]
RequireAnalyticsView = Annotated[AuthContext, Depends(require_tenant_permission(Permission.ANALYTICS_VIEW))]
RequireAiAnalysis = Annotated[AuthContext, Depends(require_tenant_permission(Permission.AI_ANALYSIS))]
RequireApiAccess = Annotated[AuthContext, Depends(require_tenant_permission(Permission.API_ACCESS))]
