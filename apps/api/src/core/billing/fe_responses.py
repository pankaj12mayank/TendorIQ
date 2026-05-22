"""Map billing domain data to frontend-friendly JSON shapes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UsageLog
from . import BillingService, PlanLimits


PLAN_DISPLAY = {
    'free': {'id': 'plan_free', 'name': 'free', 'displayName': 'Free', 'priceMonthly': 0, 'priceAnnual': 0},
    'starter': {'id': 'plan_free', 'name': 'free', 'displayName': 'Starter', 'priceMonthly': 2900, 'priceAnnual': 29000},
    'professional': {'id': 'plan_pro', 'name': 'pro', 'displayName': 'Professional', 'priceMonthly': 9900, 'priceAnnual': 99000},
    'pro': {'id': 'plan_pro', 'name': 'pro', 'displayName': 'Professional', 'priceMonthly': 9900, 'priceAnnual': 99000},
    'enterprise': {'id': 'plan_enterprise', 'name': 'enterprise', 'displayName': 'Enterprise', 'priceMonthly': 29900, 'priceAnnual': 299000},
}

FE_PLAN_TO_API = {
    'plan_free': 'starter',
    'free': 'starter',
    'starter': 'starter',
    'plan_pro': 'professional',
    'pro': 'professional',
    'professional': 'professional',
    'plan_enterprise': 'enterprise',
    'enterprise': 'enterprise',
}

QUOTA_LABELS = {
    'users': 'Team Members',
    'documents': 'Documents',
    'tenders': 'Tenders',
    'ai_tokens': 'AI Tokens',
    'api_calls': 'API Calls',
    'storage': 'Storage',
}


def normalize_plan_id(plan_id: str) -> str:
    return FE_PLAN_TO_API.get(plan_id, plan_id)


def normalize_billing_cycle(interval: str) -> str:
    if interval in ('annual', 'yearly'):
        return 'yearly'
    return 'monthly'


def fe_billing_interval(cycle: str) -> str:
    return 'annual' if cycle == 'yearly' else 'monthly'


async def get_ai_token_usage(db: AsyncSession, tenant_id: UUID) -> int:
    total = await db.scalar(
        select(func.coalesce(func.sum(UsageLog.tokens_used), 0)).where(UsageLog.tenant_id == tenant_id)
    )
    return int(total or 0)


def _quota_entry(feature_key: str, current: int, maximum: int) -> dict[str, Any]:
    is_unlimited = maximum == -1
    limit = None if is_unlimited else maximum
    remaining = None if is_unlimited else max(0, (limit or 0) - current)
    percentage = 0 if is_unlimited or not limit else min(100, int((current / limit) * 100))
    alert_level = None
    if not is_unlimited and limit:
        if current >= limit:
            alert_level = 'exceeded'
        elif percentage >= 90:
            alert_level = 'critical'
        elif percentage >= 75:
            alert_level = 'warning'
    return {
        'featureKey': feature_key,
        'featureName': QUOTA_LABELS.get(feature_key, feature_key.replace('_', ' ').title()),
        'limit': limit,
        'used': current,
        'remaining': remaining,
        'percentage': percentage,
        'isUnlimited': is_unlimited,
        'isExceeded': not is_unlimited and limit is not None and current >= limit,
        'resetPeriod': 'monthly',
        'alertLevel': alert_level,
    }


async def build_quota_list(db: AsyncSession, tenant_id: UUID) -> list[dict[str, Any]]:
    tenant_uuid = tenant_id
    sub = await BillingService.get_subscription(db, tenant_uuid)
    limits = sub['limits']
    quotas = []
    for key in ('users', 'documents', 'tenders', 'ai_tokens'):
        bucket = limits.get(key, {})
        quotas.append(_quota_entry(key, int(bucket.get('current', 0)), int(bucket.get('max', 0))))
    return quotas


async def build_usage_summary(db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
    sub = await BillingService.get_subscription(db, tenant_id)
    limits = sub['limits']
    breakdown = []
    total_usage = 0
    for key, label in QUOTA_LABELS.items():
        bucket = limits.get(key)
        if not bucket:
            continue
        count = int(bucket.get('current', 0))
        total_usage += count
        breakdown.append({
            'featureKey': key,
            'featureName': label,
            'count': count,
            'cost': 0.0,
            'percentage': 0,
        })
    if breakdown and total_usage:
        for row in breakdown:
            row['percentage'] = round((row['count'] / total_usage) * 100, 1)

    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return {
        'totalUsage': total_usage,
        'totalCost': 0.0,
        'periodStart': period_start.isoformat(),
        'periodEnd': now.isoformat(),
        'breakdown': breakdown,
    }


async def build_subscription_view(db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
    from ..models import Tenant

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise ValueError('Tenant not found')

    sub = await BillingService.get_subscription(db, tenant_id)
    plan_key = sub.get('plan') or 'starter'
    meta = PLAN_DISPLAY.get(plan_key, PLAN_DISPLAY['starter'])
    now = datetime.now(timezone.utc)
    cycle = getattr(tenant, 'billing_cycle', None) or sub.get('billing_cycle') or 'monthly'
    status = tenant.subscription_status or sub.get('status') or 'active'

    return {
        'id': tenant.subscription_id or f'sub-{tenant_id}',
        'userId': str(tenant_id),
        'planId': meta['id'],
        'plan': {
            **meta,
            'description': f'{meta["displayName"]} plan',
            'currency': 'USD',
            'trialDays': 14,
            'isActive': True,
            'features': [],
        },
        'status': 'canceled' if status == 'canceled' else 'active',
        'billingInterval': fe_billing_interval(cycle),
        'currentPeriodStart': (now - timedelta(days=15)).isoformat(),
        'currentPeriodEnd': (now + timedelta(days=15)).isoformat(),
        'cancelAtPeriodEnd': status == 'canceled',
        'createdAt': (tenant.created_at or now).isoformat() if tenant.created_at else now.isoformat(),
        'updatedAt': (tenant.updated_at or now).isoformat() if tenant.updated_at else now.isoformat(),
        'limits': sub.get('limits'),
    }


def build_plans_for_fe() -> list[dict[str, Any]]:
    plans = []
    for api_id, price in (('starter', 29), ('professional', 99), ('enterprise', 299)):
        meta = PLAN_DISPLAY.get(api_id, PLAN_DISPLAY['starter'])
        limits = PlanLimits.get_limits(api_id)
        plans.append({
            'id': meta['id'],
            'name': meta['name'],
            'displayName': meta['displayName'],
            'description': f'{meta["displayName"]} subscription',
            'priceMonthly': price * 100,
            'priceAnnual': price * 100 * 10,
            'currency': 'USD',
            'trialDays': 14 if api_id != 'enterprise' else 30,
            'isActive': True,
            'features': [
                {'key': k, 'name': QUOTA_LABELS.get(k, k), 'limit': v if v != -1 else None, 'unit': '', 'isEnabled': True}
                for k, v in limits.items()
                if k in ('users', 'documents', 'tenders', 'ai_tokens')
            ],
            'apiPlanId': api_id,
        })
    return plans
