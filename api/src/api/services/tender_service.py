"""Tender Service — user-scoped (Lite MVP)."""

from typing import Any, Optional
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService
from ...core.logging import get_logger
from ...core.lite_scope import user_owns_row
from ...core.models import Tender

logger = get_logger('tender_service')


class TenderService(BaseService):
    """Service for managing tenders (scoped by owner_id)."""

    def __init__(
        self,
        db: AsyncSession,
        user_id: str,
        tenant_id: Optional[str] = None,
        *,
        is_super_admin: bool = False,
    ):
        if not user_id:
            raise ValueError('user_id is required for TenderService')
        super().__init__(db, Tender)
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.is_super_admin = is_super_admin

    def _list_filters(self, filters: Optional[dict[str, Any]]) -> dict[str, Any]:
        merged = dict(filters or {})
        if not self.is_super_admin:
            merged['owner_id'] = self.user_id
        elif self.tenant_id:
            merged.setdefault('tenant_id', self.tenant_id)
        return merged

    def _can_access(self, tender: Tender) -> bool:
        if self.is_super_admin:
            return True
        return user_owns_row(tender, self.user_id)

    async def list_tenders(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> tuple[list[dict], int]:
        skip = (page - 1) * limit
        merged = self._list_filters(filters)

        items = await self.get_all(skip=skip, limit=limit, filters=merged)
        total = await self.count(merged)

        return [self._tender_to_dict(t) for t in items], total

    async def get_tender(self, tender_id: str) -> Optional[dict]:
        tender = await self.get(tender_id)
        if not tender or not self._can_access(tender):
            return None
        return self._tender_to_dict(tender)

    async def create_tender(self, data: dict[str, Any]) -> dict:
        if not data.get('title'):
            raise ValueError('Tender title is required')
        data['created_by_id'] = self.user_id
        data['owner_id'] = self.user_id
        if self.tenant_id:
            data['tenant_id'] = self.tenant_id

        tender = await self.create(data)
        return self._tender_to_dict(tender)

    def _assert_can_modify(self, tender: Tender, membership_role: Optional[str]) -> None:
        if self.is_super_admin:
            return
        if not user_owns_row(tender, self.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You may only modify tenders you own',
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
        if not self._can_access(tender):
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
        if not self._can_access(tender):
            return False
        self._assert_can_modify(tender, membership_role)
        return await self.delete(tender_id)

    def _tender_to_dict(self, tender: Any) -> dict:
        tid = getattr(tender, 'tenant_id', '') or ''
        owner = getattr(tender, 'owner_id', None)
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
            'ownerId': str(owner) if owner else None,
            'createdAt': _iso(created),
            'updatedAt': _iso(updated),
        }


async def get_tender_service(
    db: AsyncSession,
    user_id: str,
    tenant_id: Optional[str] = None,
    *,
    is_super_admin: bool = False,
) -> AsyncGenerator[TenderService, None]:
    yield TenderService(db, user_id, tenant_id, is_super_admin=is_super_admin)
