"""Reusable FastAPI dependency guards for subscription and quota enforcement."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Tenant, pk_str
from .lite_usage import check_quota_allowed, resolve_plan_limits
from .subscription_access import evaluate_tenant_access


async def require_active_subscription(
    tenant_id: UUID,
    db: AsyncSession,
    *,
    is_super_admin: bool = False,
) -> None:
    """Guard: block operations when subscription is expired (not when limit exceeded)."""
    if is_super_admin:
        return
    tenant = await db.get(Tenant, pk_str(tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail='Workspace not found')
    access = evaluate_tenant_access(tenant)
    if not access['can_use_system']:
        raise HTTPException(
            status_code=402,
            detail={
                'code': 'SUBSCRIPTION_EXPIRED',
                'message': access['reason'],
                'plan': access['plan'],
                'status': access['status'],
                'upgrade_required': True,
            },
        )


async def require_quota(
    tenant_id: UUID,
    operation: str,
    db: AsyncSession,
    *,
    tokens_to_add: int = 0,
) -> None:
    """Guard: block operations when plan quota is exceeded. Checks subscription too."""
    allowed, message = await check_quota_allowed(
        db, tenant_id, operation, tokens_to_add=tokens_to_add
    )
    if allowed:
        return
    tenant = await db.get(Tenant, pk_str(tenant_id))
    access = evaluate_tenant_access(tenant) if tenant else {}
    raise HTTPException(
        status_code=402,
        detail={
            'code': 'QUOTA_EXCEEDED',
            'message': message,
            'plan': access.get('plan', 'free'),
            'upgrade_required': True,
        },
    )
