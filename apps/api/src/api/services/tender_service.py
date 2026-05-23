"""Tender Service"""

from typing import Any, Optional
from collections.abc import AsyncGenerator

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService
from ...core.logging import get_logger
from ...core.models import Tender
from ...core.row_access import can_modify_tenant_resource

logger = get_logger('tender_service')


class TenderService(BaseService):
    """Service for managing tenders"""

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: Optional[str] = None):
        if not tenant_id:
            raise ValueError('tenant_id is required for TenderService')
        super().__init__(db, Tender)
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def list_tenders(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> tuple[list[dict], int]:
        skip = (page - 1) * limit
        filters = filters or {}
        filters['tenant_id'] = self.tenant_id

        items = await self.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.count(filters)

        return [self._tender_to_dict(t) for t in items], total

    async def get_tender(self, tender_id: str) -> Optional[dict]:
        tender = await self.get(tender_id)
        if tender and getattr(tender, 'tenant_id', None) != self.tenant_id:
            return None
        return self._tender_to_dict(tender) if tender else None

    async def create_tender(self, data: dict[str, Any]) -> dict:
        if not data.get('title'):
            raise ValueError('Tender title is required')
        data['created_by_id'] = self.user_id
        data['tenant_id'] = self.tenant_id

        tender = await self.create(data)
        return self._tender_to_dict(tender)

    def _assert_can_modify(self, tender: Tender, membership_role: Optional[str]) -> None:
        if not self.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='User context required to modify tenders',
            )
        if not can_modify_tenant_resource(
            user_id=self.user_id,
            membership_role=membership_role,
            created_by_id=getattr(tender, 'created_by_id', None),
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You may only modify tenders you created',
            )

    async def update_tender(
        self,
        tender_id: str,
        data: dict[str, Any],
        *,
        membership_role: Optional[str] = None,
    ) -> Optional[dict]:
        tender = await self.get(tender_id)
        if not tender:
            return None
        if getattr(tender, 'tenant_id', None) != self.tenant_id:
            return None
        self._assert_can_modify(tender, membership_role)
        tender = await self.update(tender_id, data)
        return self._tender_to_dict(tender) if tender else None

    async def delete_tender(
        self,
        tender_id: str,
        *,
        membership_role: Optional[str] = None,
    ) -> bool:
        tender = await self.get(tender_id)
        if not tender:
            return False
        if getattr(tender, 'tenant_id', None) != self.tenant_id:
            return False
        self._assert_can_modify(tender, membership_role)
        return await self.delete(tender_id)

    def _tender_to_dict(self, tender: Any) -> dict:
        tid = getattr(tender, 'tenant_id', '') or ''
        created = getattr(tender, 'created_at', None)
        updated = getattr(tender, 'updated_at', None)
        closing = getattr(tender, 'closing_date', None)

        def _iso(value: Any) -> Optional[str]:
            if value is None:
                return None
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)

        return {
            'id': str(getattr(tender, 'id', '')),
            'title': getattr(tender, 'title', ''),
            'description': getattr(tender, 'description', '') or '',
            'status': getattr(tender, 'status', 'draft'),
            'budget': getattr(tender, 'budget'),
            'currency': getattr(tender, 'currency', 'USD'),
            'closingDate': _iso(closing),
            'tenantId': str(tid),
            'organizationId': str(tid),
            'createdAt': _iso(created),
            'updatedAt': _iso(updated),
        }


async def get_tender_service(
    db: AsyncSession,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AsyncGenerator[TenderService, None]:
    yield TenderService(db, tenant_id, user_id)
