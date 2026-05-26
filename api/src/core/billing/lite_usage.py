"""Lite billing — demo quotas, usage tracking, enforcement."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Tenant, UsageLog

logger = logging.getLogger(__name__)

# Demo / free plan limits (personal workspace default)
LITE_DEMO_LIMITS: dict[str, dict[str, int]] = {
    'free': {
        'documents_per_month': 10,
        'ai_analyses_per_month': 5,
        'proposals_per_month': 3,
        'exports_per_month': 10,
        'ai_tokens_per_month': 50_000,
    },
    'starter': {
        'documents_per_month': 100,
        'ai_analyses_per_month': 50,
        'proposals_per_month': 25,
        'exports_per_month': 100,
        'ai_tokens_per_month': 500_000,
    },
    'professional': {
        'documents_per_month': 500,
        'ai_analyses_per_month': 200,
        'proposals_per_month': 100,
        'exports_per_month': 500,
        'ai_tokens_per_month': 2_000_000,
    },
    'enterprise': {
        'documents_per_month': -1,
        'ai_analyses_per_month': -1,
        'proposals_per_month': -1,
        'exports_per_month': -1,
        'ai_tokens_per_month': -1,
    },
}

ACTION_TO_LIMIT_KEY = {
    'upload_document': 'documents_per_month',
    'ai_analysis': 'ai_analyses_per_month',
    'proposal_generate': 'proposals_per_month',
    'export_pdf': 'exports_per_month',
}

ACTION_TO_USAGE_ACTION = {
    'upload_document': 'upload_document',
    'ai_analysis': 'ai_analysis',
    'proposal_generate': 'proposal_generate',
    'export_pdf': 'export',
}


def _month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_plan_limits(plan: str) -> dict[str, int]:
    return LITE_DEMO_LIMITS.get(plan or 'free', LITE_DEMO_LIMITS['free'])


async def resolve_plan_limits(db: AsyncSession, plan: str) -> dict[str, int]:
    """Merge built-in limits with admin-configured demo_limits when present."""
    base = dict(get_plan_limits(plan))
    try:
        from ..platform.lite_settings import get_setting

        demo_cfg = await get_setting(db, 'demo_limits')
        override = demo_cfg.get(plan or 'free') or demo_cfg.get('free')
        if isinstance(override, dict):
            for k, v in override.items():
                if k in base and isinstance(v, int):
                    base[k] = v
    except Exception:
        logger.debug('Using default plan limits (platform settings unavailable)', exc_info=True)
    return base


async def count_monthly_usage(
    db: AsyncSession,
    tenant_id: UUID,
    action: str,
) -> int:
    start = _month_start()
    q = select(func.count(UsageLog.id)).where(
        UsageLog.tenant_id == tenant_id,
        UsageLog.action == action,
        UsageLog.created_at >= start,
    )
    return int(await db.scalar(q) or 0)


async def count_ai_tokens_month(db: AsyncSession, tenant_id: UUID) -> int:
    start = _month_start()
    total = await db.scalar(
        select(func.coalesce(func.sum(UsageLog.tokens_used), 0)).where(
            UsageLog.tenant_id == tenant_id,
            UsageLog.created_at >= start,
        )
    )
    return int(total or 0)


async def track_usage(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: Optional[UUID],
    action: str,
    resource_type: str = 'billing',
    resource_id: Optional[UUID] = None,
    tokens_used: int = 0,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    row = UsageLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        tokens_used=tokens_used or None,
        metadata_json=metadata or {},
    )
    db.add(row)
    await db.flush()


async def check_quota_allowed(
    db: AsyncSession,
    tenant_id: UUID,
    operation: str,
    *,
    tokens_to_add: int = 0,
) -> tuple[bool, str]:
    from .subscription_access import evaluate_tenant_access

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        return False, 'Workspace not found'

    from .subscription_access import subscription_expiry_enforced

    if subscription_expiry_enforced():
        access = evaluate_tenant_access(tenant)
        if not access['can_use_system']:
            return False, access['reason']

    plan = tenant.plan or 'free'
    limits = await resolve_plan_limits(db, plan)
    limit_key = ACTION_TO_LIMIT_KEY.get(operation)
    usage_action = ACTION_TO_USAGE_ACTION.get(operation, operation)

    if limit_key:
        max_val = limits.get(limit_key, 0)
        if max_val != -1:
            current = await count_monthly_usage(db, tenant_id, usage_action)
            if current >= max_val:
                return (
                    False,
                    f'Plan limit reached for {limit_key.replace("_", " ")} ({current}/{max_val}). '
                    f'Upgrade your plan on Billing.',
                )

    token_max = limits.get('ai_tokens_per_month', -1)
    if tokens_to_add and token_max != -1:
        used = await count_ai_tokens_month(db, tenant_id)
        if used + tokens_to_add > token_max:
            return False, 'AI token quota reached for this month. Upgrade on Billing.'

    return True, ''


async def enforce_quota(
    db: AsyncSession,
    tenant_id: UUID,
    operation: str,
    *,
    tokens_to_add: int = 0,
) -> None:
    from .subscription_access import evaluate_tenant_access

    allowed, message = await check_quota_allowed(
        db, tenant_id, operation, tokens_to_add=tokens_to_add
    )
    if allowed:
        return

    tenant = await db.get(Tenant, tenant_id)
    access = evaluate_tenant_access(tenant)
    if not access['can_use_system']:
        raise HTTPException(
            status_code=402,
            detail={
                'code': 'SUBSCRIPTION_EXPIRED',
                'message': access['reason'] or message,
                'plan': access['plan'],
                'status': access['status'],
                'upgrade_required': True,
            },
        )
    raise HTTPException(
        status_code=402,
        detail={
            'code': 'QUOTA_EXCEEDED',
            'message': message,
            'plan': access['plan'],
            'upgrade_required': True,
        },
    )


async def build_demo_status(db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
    tenant = await db.get(Tenant, tenant_id)
    plan = (tenant.plan if tenant else None) or 'free'
    limits = await resolve_plan_limits(db, plan)
    usage_rows = []
    for op, limit_key in ACTION_TO_LIMIT_KEY.items():
        usage_action = ACTION_TO_USAGE_ACTION[op]
        current = await count_monthly_usage(db, tenant_id, usage_action)
        maximum = limits.get(limit_key, 0)
        usage_rows.append(
            {
                'operation': op,
                'featureKey': limit_key,
                'used': current,
                'limit': None if maximum == -1 else maximum,
                'remaining': None if maximum == -1 else max(0, maximum - current),
                'isExceeded': maximum != -1 and current >= maximum,
            }
        )
    tokens_used = await count_ai_tokens_month(db, tenant_id)
    token_max = limits.get('ai_tokens_per_month', -1)
    from .subscription_access import evaluate_tenant_access

    access = evaluate_tenant_access(tenant)
    return {
        'plan': plan,
        'is_demo': plan == 'free',
        'limits': limits,
        'usage': usage_rows,
        'ai_tokens': {
            'used': tokens_used,
            'limit': None if token_max == -1 else token_max,
        },
        'access': access,
    }
