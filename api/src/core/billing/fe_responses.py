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
    'free': {'id': 'plan_starter', 'name': 'starter', 'displayName': 'Starter', 'priceMonthly': 2900, 'priceAnnual': 29000},
    'starter': {'id': 'plan_starter', 'name': 'starter', 'displayName': 'Starter', 'priceMonthly': 2900, 'priceAnnual': 29000},
    'professional': {'id': 'plan_pro', 'name': 'pro', 'displayName': 'Professional', 'priceMonthly': 9900, 'priceAnnual': 99000},
    'pro': {'id': 'plan_pro', 'name': 'pro', 'displayName': 'Professional', 'priceMonthly': 9900, 'priceAnnual': 99000},
    'enterprise': {'id': 'plan_enterprise', 'name': 'enterprise', 'displayName': 'Enterprise', 'priceMonthly': 29900, 'priceAnnual': 299000},
}

FE_PLAN_TO_API = {
    'plan_starter': 'starter',
    'plan_free': 'starter',  # backward compatibility
    'free': 'starter',  # backward compatibility
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
    return 'monthly'


def fe_billing_interval(cycle: str) -> str:
    return 'monthly'


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
    from ..models import Tenant, pk_str

    tenant = await db.get(Tenant, pk_str(tenant_id))
    if not tenant:
        raise ValueError('Tenant not found')

    from .subscription_access import evaluate_tenant_access, period_end_from_tenant

    sub = await BillingService.get_subscription(db, tenant_id)
    plan_key = (tenant.plan or sub.get('plan') or 'free').strip().lower()
    meta = PLAN_DISPLAY.get(plan_key, PLAN_DISPLAY.get('starter', PLAN_DISPLAY['starter']))
    now = datetime.now(timezone.utc)
    cycle = getattr(tenant, 'billing_cycle', None) or sub.get('billing_cycle') or 'monthly'
    raw_status = (tenant.subscription_status or sub.get('status') or 'active').strip().lower()
    access = evaluate_tenant_access(tenant)

    settings = tenant.settings if isinstance(tenant.settings, dict) else {}
    period_start_raw = settings.get('plan_period_start')
    period_end_dt = period_end_from_tenant(tenant)
    if sub.get('current_period_start'):
        period_start = sub['current_period_start']
        if hasattr(period_start, 'isoformat'):
            period_start = period_start.isoformat()
    elif period_start_raw:
        period_start = period_start_raw
    else:
        period_start = (now - timedelta(days=15)).isoformat()

    if period_end_dt:
        period_end = period_end_dt.isoformat()
    elif sub.get('current_period_end'):
        period_end = sub['current_period_end']
        if hasattr(period_end, 'isoformat'):
            period_end = period_end.isoformat()
    else:
        period_end = (now + timedelta(days=15)).isoformat()

    fe_status = raw_status
    if access['is_expired']:
        fe_status = 'expired'
    elif raw_status in ('canceled', 'cancelled'):
        fe_status = 'canceled'

    return {
        'id': tenant.subscription_id or f'sub-{tenant_id}',
        'userId': str(tenant_id),
        'planId': meta['id'],
        'plan': {
            **meta,
            'description': f'{meta["displayName"]} plan',
            'currency': 'USD',
            'trialDays': 0,
            'isActive': not access['is_expired'],
            'features': [],
        },
        'status': fe_status,
        'billingInterval': 'monthly',
        'currentPeriodStart': period_start,
        'currentPeriodEnd': period_end,
        'cancelAtPeriodEnd': raw_status in ('canceled', 'cancelled'),
        'createdAt': (tenant.created_at or now).isoformat() if tenant.created_at else now.isoformat(),
        'updatedAt': (tenant.updated_at or now).isoformat() if tenant.updated_at else now.isoformat(),
        'limits': sub.get('limits'),
        'canUseSystem': access['can_use_system'],
        'isExpired': access['is_expired'],
        'upgradeRequired': access['upgrade_required'],
    }


def build_plans_from_pricing(pricing: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Plans shown to customers — sourced from owner Pricing settings when available."""
    raw_plans = (pricing or {}).get('plans') if isinstance(pricing, dict) else None
    if isinstance(raw_plans, list) and raw_plans:
        from .lite_usage import LITE_DEMO_LIMITS

        built: list[dict[str, Any]] = []
        for row in raw_plans:
            if not isinstance(row, dict):
                continue
            if row.get('active') is False:
                continue
            api_id = normalize_plan_id(str(row.get('id') or 'professional'))
            meta = PLAN_DISPLAY.get(api_id, PLAN_DISPLAY['professional'])
            monthly_usd = row.get('monthly_usd')
            if monthly_usd is None:
                monthly_usd = row.get('monthly_inr')
            monthly_usd = int(monthly_usd or 0)
            limits = PlanLimits.get_limits(api_id)
            lite_limits = LITE_DEMO_LIMITS.get(api_id, limits)
            built.append(
                {
                    'id': meta['id'] if str(row.get('id', '')).startswith('plan_') else f"plan_{api_id}",
                    'name': meta['name'],
                    'displayName': str(row.get('name') or meta['displayName']),
                    'description': str(row.get('description') or f'{meta["displayName"]} subscription'),
                    'priceMonthly': monthly_usd * 100,
                    'priceAnnual': monthly_usd * 100,
                    'priceMonthlyUsd': monthly_usd,
                    'priceAnnualUsd': monthly_usd,
                    'currency': str((pricing or {}).get('currency') or 'USD'),
                    'isDemo': False,
                    'trialDays': 0,
                    'isActive': True,
                    'expiryPeriodDays': int(row.get('expiry_period_days') or 30),
                    'features': [
                        {'key': f'feature_{i}', 'name': str(f), 'limit': None, 'unit': '/mo', 'isEnabled': True}
                        for i, f in enumerate(row.get('features') or [])
                    ]
                    or [
                        {
                            'key': k,
                            'name': QUOTA_LABELS.get(k, k.replace('_per_month', '')),
                            'limit': v if v != -1 else None,
                            'unit': '/mo',
                            'isEnabled': True,
                        }
                        for k, v in lite_limits.items()
                        if k.endswith('_per_month') or k in ('users', 'documents', 'tenders', 'ai_tokens')
                    ],
                    'apiPlanId': api_id,
                }
            )
        if built:
            return built
    return build_plans_for_fe()


def build_plans_for_fe() -> list[dict[str, Any]]:
    plans = []
    for api_id, price_usd in (('starter', 29), ('professional', 99), ('enterprise', 299)):
        meta = PLAN_DISPLAY.get(api_id, PLAN_DISPLAY['starter'])
        limits = PlanLimits.get_limits(api_id)
        from .lite_usage import LITE_DEMO_LIMITS

        lite_limits = LITE_DEMO_LIMITS.get(api_id, limits)
        plans.append({
            'id': meta['id'],
            'name': meta['name'],
            'displayName': meta['displayName'],
            'description': f'{meta["displayName"]} subscription',
            'priceMonthly': price_usd * 100,
            'priceAnnual': price_usd * 100,
            'priceMonthlyUsd': price_usd,
            'priceAnnualUsd': price_usd,
            'currency': 'USD',
            'isDemo': False,
            'trialDays': 0,
            'isActive': True,
            'features': [
                {'key': k, 'name': QUOTA_LABELS.get(k, k.replace('_per_month', '')), 'limit': v if v != -1 else None, 'unit': '/mo', 'isEnabled': True}
                for k, v in lite_limits.items()
                if k.endswith('_per_month') or k in ('users', 'documents', 'tenders', 'ai_tokens')
            ],
            'apiPlanId': api_id,
        })
    return plans
