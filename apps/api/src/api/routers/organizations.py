\"\"\"Organizations API Router\"\"\"

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..dependencies.auth import CurrentUser, TenantID
from ..schemas.base import create_response, PaginatedResponse, PaginationMeta
from ...core.database import get_db
from ...core.models import Tenant

router = APIRouter(prefix='/organizations', tags=['Organizations'])


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    website: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    website: Optional[str] = None
    created_at: str


@router.get('', response_model=PaginatedResponse)
async def list_organizations(
    current_user: CurrentUser,
    tenant_id: TenantID,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    offset = (page - 1) * limit
    stmt = select(Tenant).where(Tenant.id == tenant_id).offset(offset).limit(limit)
    result = await db.execute(stmt)
    tenants = result.scalars().all()

    count_stmt = select(func.count(Tenant.id)).where(Tenant.id == tenant_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    items = []
    for tenant in tenants:
        items.append({
            'id': str(tenant.id),
            'name': tenant.name,
            'slug': tenant.slug,
            'description': tenant.description or '',
            'website': tenant.website or '',
            'created_at': tenant.created_at.isoformat() if tenant.created_at else '',
        })

    return create_response(
        items,
        PaginationMeta(page=page, limit=limit, total=total, total_pages=(total + limit - 1) // limit),
    )


@router.get('/{organization_id}', response_model=dict)
async def get_organization(
    organization_id: str,
    current_user: CurrentUser,
    tenant_id: TenantID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    tenant = await db.get(Tenant, organization_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')

    return create_response({
        'id': str(tenant.id),
        'name': tenant.name,
        'slug': tenant.slug,
        'description': tenant.description or '',
        'website': tenant.website or '',
        'created_at': tenant.created_at.isoformat() if tenant.created_at else '',
    })


@router.post('', response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: CurrentUser,
    tenant_id: TenantID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    existing = await db.execute(select(Tenant).where(Tenant.slug == org_data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Organization with this slug already exists')

    tenant = Tenant(
        name=org_data.name,
        slug=org_data.slug,
        description=org_data.description,
        website=org_data.website,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return create_response({
        'id': str(tenant.id),
        'name': tenant.name,
        'slug': tenant.slug,
        'description': tenant.description or '',
        'website': tenant.website or '',
        'created_at': tenant.created_at.isoformat() if tenant.created_at else '',
    })


@router.patch('/{organization_id}', response_model=dict)
async def update_organization(
    organization_id: str,
    org_data: OrganizationUpdate,
    current_user: CurrentUser,
    tenant_id: TenantID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    tenant = await db.get(Tenant, organization_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')

    update_data = org_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)

    await db.commit()
    await db.refresh(tenant)

    return create_response({
        'id': str(tenant.id),
        'name': tenant.name,
        'slug': tenant.slug,
        'description': tenant.description or '',
        'website': tenant.website or '',
        'created_at': tenant.created_at.isoformat() if tenant.created_at else '',
    })


@router.delete('/{organization_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    current_user: CurrentUser,
    tenant_id: TenantID,
    db: AsyncSession = Depends(get_db),
) -> None:
    tenant = await db.get(Tenant, organization_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Organization not found')

    await db.delete(tenant)
    await db.commit()
