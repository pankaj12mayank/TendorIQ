"""Repair tenant billing rows after bad migrations / dev experiments."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import Tenant
from ..user_preferences import normalize_preferences
from .subscription_access import ACTIVE_STATUSES, apply_plan_period, period_end_from_tenant


def _tenant_settings(tenant: Tenant) -> dict:
    return normalize_preferences(tenant.settings)


async def repair_tenant_billing_state(db: AsyncSession) -> bool:
    """Normalize subscription fields so dev/local tenants are usable."""
    settings = get_settings()
    changed = False
    now = datetime.now(timezone.utc)

    tenants = (await db.execute(select(Tenant))).scalars().all()
    for tenant in tenants:
        prefs = _tenant_settings(tenant)
        if prefs != tenant.settings:
            tenant.settings = prefs
            changed = True

        plan = (tenant.plan or 'free').strip().lower()
        status = (tenant.subscription_status or '').strip().lower()

        if not status or status not in ACTIVE_STATUSES and status not in (
            'expired',
            'canceled',
            'cancelled',
            'past_due',
            'unpaid',
        ):
            tenant.subscription_status = 'active'
            changed = True

        if plan == 'free':
            continue

        # Demo workspace: keep generous dev plan
        if settings.is_development and (tenant.slug or '').lower() == (
            settings.DEMO_TENANT_SLUG or 'demo'
        ).lower():
            if tenant.plan != 'professional':
                tenant.plan = 'professional'
                changed = True

        period_end = period_end_from_tenant(tenant)
        if not period_end and settings.is_development:
            cycle = (tenant.billing_cycle or 'monthly').strip().lower()
            apply_plan_period(tenant, billing_cycle=cycle)
            changed = True
        elif period_end and period_end < now and settings.is_development:
            # Refresh stale dev periods so local testing is not locked out
            cycle = (tenant.billing_cycle or 'monthly').strip().lower()
            apply_plan_period(tenant, billing_cycle=cycle, start=now)
            if tenant.subscription_status in ('expired', 'canceled', 'cancelled'):
                tenant.subscription_status = 'active'
            changed = True

    if changed:
        await db.commit()
    return changed
