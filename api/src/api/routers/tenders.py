"""Tenders API Router"""

from typing import Optional

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ...core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.access import TenantUser, require_tenant_member
from ..schemas.base import (
    create_response,
    PaginatedResponse,
    PaginationMeta,
)
from ..schemas.tender import (
    TenderCreate,
    TenderUpdate,
)
from ..services.tender_service import TenderService
from ...core.database import get_db

router = APIRouter(
    prefix='/tenders',
    tags=['Tenders'],
    dependencies=[Depends(require_tenant_member)],
)
logger = get_logger('tenders_api')


@router.get('', response_model=PaginatedResponse)
async def list_tenders(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> dict:
    service = TenderService(
        db=db,
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        is_super_admin=current_user.is_super_admin(),
    )

    filters = {}
    if status:
        filters['status'] = status

    items, total = await service.list_tenders(
        page=page,
        limit=limit,
        filters=filters,
    )

    meta = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=(total + limit - 1) // limit,
    )

    return create_response(items, meta)


@router.get('/{tender_id}', response_model=dict)
async def get_tender(
    tender_id: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = TenderService(
        db=db,
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        is_super_admin=current_user.is_super_admin(),
    )
    tender = await service.get_tender(tender_id)

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tender not found',
        )

    return create_response(tender)


@router.post('', response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_tender(
    tender_data: TenderCreate,
    current_user: TenantUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = TenderService(db=db, tenant_id=current_user.tenant_id, user_id=current_user.user_id)

    payload = tender_data.model_dump(exclude_none=True)
    payload.pop('organization_id', None)
    tender = await service.create_tender(payload)
    return create_response(tender)


@router.patch('/{tender_id}', response_model=dict)
async def update_tender(
    tender_id: str,
    tender_data: TenderUpdate,
    current_user: TenantUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = TenderService(db=db, tenant_id=current_user.tenant_id, user_id=current_user.user_id)

    before = await service.get_tender(tender_id)
    patch = tender_data.model_dump(exclude_unset=True)
    tender = await service.update_tender(
        tender_id,
        patch,
        membership_role=current_user.membership_role,
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tender not found',
        )

    old_values = {k: before.get(k) for k in patch.keys()} if before else {}
    return create_response(tender)


@router.delete('/{tender_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender(
    tender_id: str,
    current_user: TenantUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = TenderService(db=db, tenant_id=current_user.tenant_id, user_id=current_user.user_id)
    existing = await service.get_tender(tender_id)

    success = await service.delete_tender(
        tender_id,
        membership_role=current_user.membership_role,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tender not found',
        )

