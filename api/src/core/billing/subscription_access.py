"""Plan subscription state — login allowed, usage blocked when expired."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Subscription, Tenant

FREE_PLAN = 'free'
PAID_PLANS = frozenset({'starter', 'professional', 'enterprise', 'pro'})
ACTIVE_STATUSES = frozenset({'active', 'trialing'})
BLOCKED_STATUSES = frozenset({'expired', 'canceled', 'cancelled', 'past_due', 'unpaid'})


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _tenant_settings(tenant: Tenant) -> dict[str, Any]:
    from ..user_preferences import normalize_preferences

    return normalize_preferences(tenant.settings)


def subscription_expiry_enforced() -> bool:
    from ..config import get_settings

    return get_settings().billing_enforce_subscription_expiry


def period_end_from_tenant(tenant: Tenant) -> Optional[datetime]:
    settings = _tenant_settings(tenant)
    end = _parse_iso(settings.get('plan_period_end'))
    if end:
        return end
    return None


def compute_period_end(*, billing_cycle: str, start: Optional[datetime] = None) -> datetime:
    from datetime import timedelta

    base = start or datetime.now(timezone.utc)
    if billing_cycle in ('yearly', 'annual'):
        return base + timedelta(days=365)
    return base + timedelta(days=30)


def apply_plan_period(
    tenant: Tenant,
    *,
    billing_cycle: str,
    start: Optional[datetime] = None,
) -> tuple[datetime, datetime]:
    """Persist plan period on tenant.settings (used for expiry checks)."""
    begin = start or datetime.now(timezone.utc)
    end = compute_period_end(billing_cycle=billing_cycle, start=begin)
    settings = _tenant_settings(tenant)
    settings['plan_period_start'] = begin.isoformat()
    settings['plan_period_end'] = end.isoformat()
    tenant.settings = settings
    return begin, end


async def sync_subscription_row(
    db: AsyncSession,
    tenant: Tenant,
    *,
    plan: str,
    status: str,
    billing_cycle: str,
    period_start: datetime,
    period_end: datetime,
) -> None:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.tenant_id == tenant.id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        sub = Subscription(
            tenant_id=tenant.id,
            plan=plan,
            status=status,
            billing_cycle=billing_cycle,
            amount=0.0,
        )
        db.add(sub)
    sub.plan = plan
    sub.status = status
    sub.billing_cycle = billing_cycle
    sub.current_period_start = period_start
    sub.current_period_end = period_end
    sub.cancelled_at = None
    sub.cancel_at_period_end = False


def evaluate_tenant_access(tenant: Optional[Tenant]) -> dict[str, Any]:
    """Return whether tenant may use product features (not login)."""
    if not tenant:
        return {
            'can_use_system': False,
            'is_expired': True,
            'plan': FREE_PLAN,
            'status': 'expired',
            'reason': 'Workspace not found',
            'upgrade_required': True,
        }

    plan = (tenant.plan or FREE_PLAN).strip().lower()
    status = (tenant.subscription_status or 'active').strip().lower() or 'active'
    period_end = period_end_from_tenant(tenant)
    now = datetime.now(timezone.utc)

    if not subscription_expiry_enforced():
        return {
            'can_use_system': True,
            'is_expired': False,
            'plan': plan,
            'status': status,
            'reason': '',
            'upgrade_required': False,
            'period_end': period_end.isoformat() if period_end else None,
            'enforcement': 'quotas_only',
        }

    if plan == FREE_PLAN:
        return {
            'can_use_system': True,
            'is_expired': False,
            'plan': plan,
            'status': status or 'active',
            'reason': '',
            'upgrade_required': False,
            'period_end': period_end.isoformat() if period_end else None,
        }

    # Paid plan: explicit blocked status
    if status in BLOCKED_STATUSES:
        return {
            'can_use_system': False,
            'is_expired': True,
            'plan': plan,
            'status': status,
            'reason': 'Your paid plan is not active. Renew or upgrade on Billing.',
            'upgrade_required': True,
            'period_end': period_end.isoformat() if period_end else None,
        }

    if period_end and now > period_end:
        return {
            'can_use_system': False,
            'is_expired': True,
            'plan': plan,
            'status': 'expired',
            'reason': 'Your plan period has ended. Upgrade or renew on Billing to continue.',
            'upgrade_required': True,
            'period_end': period_end.isoformat(),
        }

    if status not in ACTIVE_STATUSES:
        return {
            'can_use_system': False,
            'is_expired': True,
            'plan': plan,
            'status': status,
            'reason': 'Subscription inactive. Update your plan on Billing.',
            'upgrade_required': True,
            'period_end': period_end.isoformat() if period_end else None,
        }

    return {
        'can_use_system': True,
        'is_expired': False,
        'plan': plan,
        'status': status,
        'reason': '',
        'upgrade_required': False,
        'period_end': period_end.isoformat() if period_end else None,
    }


async def get_tenant_access(db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
    tenant = await db.get(Tenant, tenant_id)
    return evaluate_tenant_access(tenant)


async def assert_can_use_system(db: AsyncSession, tenant_id: UUID) -> None:
    """Block product usage when plan expired; login remains allowed."""
    access = await get_tenant_access(db, tenant_id)
    if access['can_use_system']:
        return
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


async def mark_subscription_expired(db: AsyncSession, tenant: Tenant) -> None:
    tenant.subscription_status = 'expired'
    await db.flush()


def apply_tenant_plan_entitlements(tenant: Tenant, plan: str) -> None:
    """Sync storage/user caps on tenant when plan changes."""
    from . import PlanLimits
    from .lite_usage import get_plan_limits

    api_plan = (plan or FREE_PLAN).strip().lower()
    if api_plan == FREE_PLAN:
        demo = get_plan_limits(FREE_PLAN)
        tenant.quota_storage_mb = 512
        tenant.quota_users = max(3, demo.get('documents_per_month', 10) // 2)
        return

    limits = PlanLimits.get_limits(api_plan)
    storage = limits.get('storage_mb', 1024)
    users = limits.get('users', 5)
    tenant.quota_storage_mb = 999_999 if storage == -1 else int(storage)
    tenant.quota_users = 999 if users == -1 else int(users)
