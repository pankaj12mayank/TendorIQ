"""Tenders API Router"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies.auth import CurrentUser, TenantID
from ..schemas.base import (
    create_error_response,
    create_response,
    PaginatedResponse,
    PaginationMeta,
)
from ..schemas.tender import (
    TenderCreate,
    TenderListResponse,
    TenderResponse,
    TenderUpdate,
)
from ..services.tender_service import TenderService

router = APIRouter(prefix='/tenders', tags=['Tenders'])


@router.get('', response_model=PaginatedResponse)
async def list_tenders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(),
    tenant_id: TenantID = None,
) -> dict:
    service = TenderService(tenant_id=tenant_id)

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
    current_user: CurrentUser = Depends(),
    tenant_id: TenantID = None,
) -> dict:
    service = TenderService(tenant_id=tenant_id)
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
    current_user: CurrentUser = Depends(),
    tenant_id: TenantID = None,
) -> dict:
    service = TenderService(tenant_id=tenant_id, user_id=current_user['id'])

    tender = await service.create_tender(tender_data.model_dump())
    return create_response(tender)


@router.patch('/{tender_id}', response_model=dict)
async def update_tender(
    tender_id: str,
    tender_data: TenderUpdate,
    current_user: CurrentUser = Depends(),
    tenant_id: TenantID = None,
) -> dict:
    service = TenderService(tenant_id=tenant_id, user_id=current_user['id'])

    tender = await service.update_tender(tender_id, tender_data.model_dump(exclude_unset=True))

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tender not found',
        )

    return create_response(tender)


@router.delete('/{tender_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender(
    tender_id: str,
    current_user: CurrentUser = Depends(),
    tenant_id: TenantID = None,
) -> None:
    service = TenderService(tenant_id=tenant_id, user_id=current_user['id'])

    success = await service.delete_tender(tender_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tender not found',
        )