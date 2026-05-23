"""Bids API — tenant bid list for dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.models import Bid, Tender
from ...core.tenant_types import parse_tenant_uuid
from ..dependencies.rbac_deps import RequireBidRead

router = APIRouter(prefix='/bids', tags=['Bids'])


def _format_amount(amount: Optional[float], currency: str = 'USD') -> str:
    if amount is None:
        return '$0.00'
    symbol = '$' if currency == 'USD' else f'{currency} '
    return f'{symbol}{amount:,.2f}'


def _status_for_ui(status: str) -> str:
    if status == 'accepted':
        return 'won'
    if status == 'rejected':
        return 'lost'
    return status


@router.get('')
async def list_bids(
    current_user: RequireBidRead,
    db: AsyncSession = Depends(get_db),
) -> dict:
    tenant_id = parse_tenant_uuid(current_user.tenant_id)
    result = await db.execute(
        select(Bid, Tender.title)
        .join(Tender, Bid.tender_id == Tender.id)
        .where(
            Bid.tenant_id == tenant_id,
            Bid.deleted_at.is_(None),
            Tender.deleted_at.is_(None),
        )
        .order_by(Bid.updated_at.desc())
        .limit(500)
    )
    rows = result.all()

    bids_out: list[dict] = []
    total_amount = 0.0
    won = 0
    pending = 0

    for bid, tender_title in rows:
        ui_status = _status_for_ui(bid.status or 'draft')
        if ui_status == 'won':
            won += 1
        if ui_status in ('submitted', 'under_review'):
            pending += 1
        if bid.amount is not None:
            total_amount += float(bid.amount)

        submitted: Optional[datetime] = bid.submitted_at or bid.created_at
        bids_out.append(
            {
                'id': str(bid.id),
                'tender': tender_title or 'Untitled tender',
                'amount': _format_amount(bid.amount, bid.currency or 'USD'),
                'status': ui_status,
                'submittedAt': submitted.isoformat() if submitted else '',
            }
        )

    total = len(bids_out)
    win_rate = round((won / total) * 100) if total else 0

    return {
        'bids': bids_out,
        'total_bids': total,
        'win_rate': win_rate,
        'total_value': _format_amount(total_amount),
        'pending_count': pending,
    }
