"""Tenant Switching API - Organization Switching Endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .dependencies.auth import CurrentUser
from .dependencies.tenant import get_tenant_context
from .services.tenant_service import tenant_service
from .services.membership_service import membership_service
from ..core.database import get_db
from ..core.models import Membership, Tenant
from ..core.rbac import Permission, RBACService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/tenants', tags=['tenants'])


class SwitchTenantRequest(BaseModel):
    tenant_id: str


class SwitchTenantResponse(BaseModel):
    success: bool
    tenant_id: str
    tenant_name: str
    role: str
    membership_id: str


class TenantListItem(BaseModel):
    id: str
    name: str
    slug: str
    role: str
    status: str
    logo_url: Optional[str] = None


class TenantListResponse(BaseModel):
    success: bool
    tenants: list[TenantListItem]
    current_tenant_id: Optional[str] = None


@router.get('/me', response_model=TenantListResponse)
async def list_my_tenants(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all tenants the current user belongs to"""
    memberships = await membership_service.get_user_memberships(
        db, 
        UUID(current_user.user_id)
    )

    tenant_ids = await membership_service.get_active_tenant_ids(
        db, 
        UUID(current_user.user_id)
    )

    from sqlalchemy import select
    result = await db.execute(
        select(Tenant).where(Tenant.id.in_(tenant_ids))
    )
    tenants = {str(t.id): t for t in result.scalars().all()}

    tenant_items = []
    for membership in memberships:
        tenant = tenants.get(str(membership.tenant_id))
        if tenant:
            tenant_items.append(TenantListItem(
                id=str(tenant.id),
                name=tenant.name,
                slug=tenant.slug,
                role=membership.role,
                status=membership.status,
                logo_url=tenant.logo_url
            ))

    return TenantListResponse(
        success=True,
        tenants=tenant_items,
        current_tenant_id=current_user.tenant_id
    )


@router.post('/switch', response_model=SwitchTenantResponse)
async def switch_tenant(
    request: SwitchTenantRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Switch active tenant context"""
    membership, tenant = await membership_service.switch_tenant(
        db,
        UUID(current_user.user_id),
        UUID(request.tenant_id)
    )

    if not membership or not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Cannot switch to this organization',
        )

    return SwitchTenantResponse(
        success=True,
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        role=membership.role,
        membership_id=str(membership.id)
    )


@router.get('/{tenant_id}', response_model=TenantListItem)
async def get_tenant(
    tenant_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get tenant details"""
    from .dependencies.tenant import verify_tenant_access
    
    valid, error = await verify_tenant_access(
        db, 
        current_user.user_id, 
        tenant_id
    )
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    tenant = await tenant_service.get_tenant_by_id(db, UUID(tenant_id))
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Organization not found',
        )

    return TenantListItem(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        role=current_user.membership_role or 'member',
        status=tenant.status,
        logo_url=tenant.logo_url
    )


@router.get('/{tenant_id}/members')
async def list_tenant_members(
    tenant_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all members of a tenant"""
    from .dependencies.tenant import verify_tenant_access
    from .dependencies.auth import check_permission
    
    valid, error = await verify_tenant_access(db, current_user.user_id, tenant_id)
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    if not check_permission(current_user, Permission.ORG_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Permission denied',
        )

    memberships = await membership_service.get_tenant_members(
        db, 
        UUID(tenant_id)
    )

    from sqlalchemy import select
    from ..core.models import User
    
    user_ids = [m.user_id for m in memberships if m.user_id]
    if user_ids:
        result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {str(u.id): u for u in result.scalars().all()}
    else:
        users = {}

    return {
        'success': True,
        'members': [
            {
                'id': str(m.id),
                'user_id': str(m.user_id) if m.user_id else None,
                'email': users.get(str(m.user_id)).email if m.user_id and users.get(str(m.user_id)) else None,
                'name': users.get(str(m.user_id)).name if m.user_id and users.get(str(m.user_id)) else None,
                'role': m.role,
                'status': m.status,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None,
            }
            for m in memberships
        ]
    }


@router.post('/{tenant_id}/members/invite')
async def invite_member(
    tenant_id: str,
    email: str,
    role: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Invite a member to the tenant"""
    from .dependencies.tenant import verify_tenant_access
    from .dependencies.auth import check_permission
    
    valid, error = await verify_tenant_access(db, current_user.user_id, tenant_id)
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    if not check_permission(current_user, Permission.USER_INVITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Permission denied',
        )

    membership = await membership_service.invite_member(
        db,
        UUID(tenant_id),
        email,
        role,
        UUID(current_user.user_id)
    )

    return {
        'success': True,
        'membership_id': str(membership.id),
        'status': membership.status
    }


@router.delete('/{tenant_id}/members/{membership_id}')
async def remove_member(
    tenant_id: str,
    membership_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the tenant"""
    from .dependencies.tenant import verify_tenant_access
    from .dependencies.auth import check_permission
    
    valid, error = await verify_tenant_access(db, current_user.user_id, tenant_id)
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    if not check_permission(current_user, Permission.ORG_MANAGE_MEMBERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Permission denied',
        )

    success = await membership_service.remove_member(
        db,
        UUID(membership_id),
        UUID(current_user.user_id)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Member not found',
        )

    return {'success': True}


@router.patch('/{tenant_id}/members/{membership_id}/role')
async def update_member_role(
    tenant_id: str,
    membership_id: str,
    role: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update a member's role"""
    from .dependencies.tenant import verify_tenant_access
    from .dependencies.auth import check_permission
    
    valid, error = await verify_tenant_access(db, current_user.user_id, tenant_id)
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    if not check_permission(current_user, Permission.ORG_MANAGE_MEMBERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Permission denied',
        )

    membership = await membership_service.update_role(
        db,
        UUID(membership_id),
        role,
        UUID(current_user.user_id)
    )

    return {
        'success': True,
        'role': membership.role
    }