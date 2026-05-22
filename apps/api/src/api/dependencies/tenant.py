"""Tenant Dependencies - FastAPI Dependency Injection for Tenants"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from ..services.tenant_service import tenant_service
from ..services.membership_service import membership_service
from ...core.middleware import get_current_tenant_id
from ...core.tenant_context import TenantQueryHelper as tenant_query
from ...core.auth import AuthContext
from .auth import get_current_user


class TenantContext:
    """Tenant context for dependency injection"""
    
    def __init__(
        self,
        tenant_id: str,
        user_id: str,
        role: str,
        membership_id: Optional[str] = None
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
        self.membership_id = membership_id

    def is_admin(self) -> bool:
        return self.role in ('owner', 'admin')

    def is_owner(self) -> bool:
        return self.role == 'owner'

    def can_manage_members(self) -> bool:
        return self.role in ('owner', 'admin')

    def to_dict(self) -> dict:
        return {
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'role': self.role,
            'membership_id': self.membership_id,
        }


async def get_tenant_context(
    request: Request,
    auth: AuthContext = Depends(get_current_user),
) -> TenantContext:
    """Get tenant context from request"""
    from ...core.middleware import get_tenant_context as get_ctx
    
    ctx = get_ctx(request)
    
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant context required',
        )
    
    return TenantContext(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        role=ctx.role
    )


async def require_tenant_id(
    request: Request,
    auth: AuthContext = Depends(get_current_user),
) -> str:
    """Require tenant ID from middleware or JWT (canonical dependency)."""
    tenant_id = get_current_tenant_id(request) or auth.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant ID is required',
        )
    return str(tenant_id)


# Backward-compatible alias
get_tenant_id = require_tenant_id


async def verify_tenant_access(
    db,
    user_id: str,
    tenant_id: str,
) -> tuple[bool, str]:
    """Verify user has access to tenant"""
    try:
        uuid_tenant = UUID(tenant_id)
    except ValueError:
        return False, 'Invalid tenant ID'

    return await tenant_query.verify_tenant_access(
        db, 
        UUID(user_id), 
        uuid_tenant
    )


async def require_tenant_access(
    db,
    auth: AuthContext = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> tuple[str, str, UUID]:
    """Dependency to verify tenant access and return validated IDs"""
    valid, error = await verify_tenant_access(db, auth.user_id, tenant_id)
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )
    
    return auth.user_id, tenant_id, UUID(tenant_id)


class TenantAwareDB:
    """Database session with tenant context"""
    
    def __init__(self, db, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id


async def get_db_with_tenant(
    db,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
) -> TenantAwareDB:
    """Get database session with tenant context"""
    tenant_id = get_current_tenant_id(request)
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant context required',
        )
    
    return TenantAwareDB(db, tenant_id)


TenantContextDep = Annotated[TenantContext, Depends(get_tenant_context)]
TenantIDDep = Annotated[str, Depends(get_tenant_id)]
DBTenantDep = Annotated[TenantAwareDB, Depends(get_db_with_tenant)]