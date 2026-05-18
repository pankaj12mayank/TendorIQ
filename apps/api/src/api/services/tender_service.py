"""Tender Service"""

from typing import Any, Optional
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService
from ...core.logging import get_logger

logger = get_logger('tender_service')


class TenderModel:
    pass


class TenderService(BaseService):
    """Service for managing tenders"""

    def __init__(self, db: AsyncSession, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(db, TenderModel)
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

        if self.tenant_id:
            filters['organization_id'] = self.tenant_id

        items = await self.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.count(filters)

        return [self._tender_to_dict(t) for t in items], total

    async def get_tender(self, tender_id: str) -> Optional[dict]:
        tender = await self.get(tender_id)
        if tender and self.tenant_id:
            if getattr(tender, 'organization_id', None) != self.tenant_id:
                return None
        return self._tender_to_dict(tender) if tender else None

    async def create_tender(self, data: dict[str, Any]) -> dict:
        data['created_by_id'] = self.user_id

        if self.tenant_id:
            data['organization_id'] = self.tenant_id

        tender = await self.create(data)
        return self._tender_to_dict(tender)

    async def update_tender(self, tender_id: str, data: dict[str, Any]) -> Optional[dict]:
        tender = await self.update(tender_id, data)
        return self._tender_to_dict(tender) if tender else None

    async def delete_tender(self, tender_id: str) -> bool:
        return await self.delete(tender_id)

    def _tender_to_dict(self, tender: Any) -> dict:
        return {
            'id': getattr(tender, 'id', ''),
            'title': getattr(tender, 'title', ''),
            'description': getattr(tender, 'description', ''),
            'status': getattr(tender, 'status', 'draft'),
            'budget': getattr(tender, 'budget'),
            'currency': getattr(tender, 'currency', 'USD'),
            'closing_date': getattr(tender, 'closing_date'),
            'organization_id': getattr(tender, 'organization_id', ''),
            'created_by_id': getattr(tender, 'created_by_id', ''),
            'created_at': getattr(tender, 'created_at'),
            'updated_at': getattr(tender, 'updated_at'),
        }


async def get_tender_service(
    db: AsyncSession,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AsyncGenerator[TenderService, None]:
    yield TenderService(db, tenant_id, user_id)