"""Apply Stripe webhook events to tenant subscription state."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Subscription, Tenant
from .fe_responses import normalize_plan_id

logger = logging.getLogger(__name__)

_STRIPE_STATUS_TO_TENANT = {
    'active': 'active',
    'trialing': 'active',
    'past_due': 'past_due',
    'canceled': 'canceled',
    'cancelled': 'canceled',
    'unpaid': 'past_due',
    'incomplete': 'past_due',
    'incomplete_expired': 'canceled',
}


def _tenant_id_from_metadata(meta: Optional[dict]) -> Optional[UUID]:
    if not meta:
        return None
    raw = meta.get('tenant_id') or meta.get('tenantId')
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


async def _tenant_by_stripe_customer(db: AsyncSession, customer_id: Optional[str]) -> Optional[Tenant]:
    if not customer_id:
        return None
    sub = (
        await db.execute(
            select(Subscription).where(Subscription.stripe_customer_id == customer_id).limit(1)
        )
    ).scalar_one_or_none()
    if not sub:
        return None
    return await db.get(Tenant, sub.tenant_id)


async def _upsert_subscription_row(
    db: AsyncSession,
    tenant: Tenant,
    *,
    plan: str,
    status: str,
    stripe_subscription_id: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
    billing_cycle: str = 'monthly',
) -> None:
    tenant.plan = normalize_plan_id(plan)
    tenant.subscription_status = _STRIPE_STATUS_TO_TENANT.get(status, status)
    if stripe_subscription_id:
        tenant.subscription_id = stripe_subscription_id

    existing = (
        await db.execute(
            select(Subscription)
            .where(Subscription.tenant_id == tenant.id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    norm_status = 'cancelled' if status in ('canceled', 'cancelled') else status
    if existing:
        existing.plan = tenant.plan
        existing.status = norm_status if norm_status in ('active', 'trialing', 'past_due', 'cancelled', 'unpaid') else 'active'
        if stripe_subscription_id:
            existing.stripe_subscription_id = stripe_subscription_id
        if stripe_customer_id:
            existing.stripe_customer_id = stripe_customer_id
        existing.billing_cycle = billing_cycle
    else:
        db.add(
            Subscription(
                tenant_id=tenant.id,
                plan=tenant.plan,
                status=norm_status if norm_status in ('active', 'trialing', 'past_due', 'cancelled', 'unpaid') else 'active',
                stripe_subscription_id=stripe_subscription_id,
                stripe_customer_id=stripe_customer_id,
                billing_cycle=billing_cycle,
                amount=0.0,
            )
        )


async def _sync_checkout_session(db: AsyncSession, session: dict[str, Any]) -> bool:
    tenant_id = _tenant_id_from_metadata(session.get('metadata'))
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    plan = normalize_plan_id((session.get('metadata') or {}).get('plan_id', 'starter'))

    tenant: Optional[Tenant] = None
    if tenant_id:
        tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        tenant = await _tenant_by_stripe_customer(db, customer_id if isinstance(customer_id, str) else None)

    if not tenant:
        logger.warning('Stripe checkout.session.completed: tenant not resolved')
        return False

    from .razorpay_lite import activate_plan_after_payment, plan_period_days
    from ..platform.lite_settings import get_setting

    pricing = await get_setting(db, 'pricing')
    period_days = await plan_period_days(db, plan, pricing)
    payment_id = str(session.get('payment_intent') or session.get('id') or '')
    await activate_plan_after_payment(
        db,
        tenant_id=tenant.id,
        plan=plan,
        billing_interval=str((session.get('metadata') or {}).get('billing_interval') or 'monthly'),
        payment_id=payment_id or 'stripe_checkout',
        order_id=str(session.get('id') or ''),
        provider='stripe',
        period_days=period_days,
    )
    if subscription_id and isinstance(subscription_id, str):
        tenant.subscription_id = subscription_id
    if customer_id and isinstance(customer_id, str):
        existing = (
            await db.execute(
                select(Subscription)
                .where(Subscription.tenant_id == tenant.id)
                .order_by(Subscription.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing:
            existing.stripe_customer_id = customer_id
    return True


async def _sync_subscription_object(db: AsyncSession, sub: dict[str, Any]) -> bool:
    stripe_sub_id = sub.get('id')
    customer_id = sub.get('customer')
    status = str(sub.get('status', 'active'))
    meta = sub.get('metadata') or {}
    plan = normalize_plan_id(meta.get('plan_id') or meta.get('plan') or 'starter')

    tenant_id = _tenant_id_from_metadata(meta)
    tenant: Optional[Tenant] = None
    if tenant_id:
        tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        tenant = await _tenant_by_stripe_customer(db, customer_id if isinstance(customer_id, str) else None)

    if not tenant:
        logger.warning('Stripe subscription event: tenant not resolved sub=%s', stripe_sub_id)
        return False

    await _upsert_subscription_row(
        db,
        tenant,
        plan=plan,
        status=status,
        stripe_subscription_id=stripe_sub_id if isinstance(stripe_sub_id, str) else None,
        stripe_customer_id=customer_id if isinstance(customer_id, str) else None,
    )
    return True


async def apply_stripe_webhook_event(db: AsyncSession, event: dict[str, Any]) -> dict[str, Any]:
    """Persist subscription changes from a verified Stripe event payload."""
    event_type = str(event.get('type', ''))
    data_obj = (event.get('data') or {}).get('object') or {}
    handled = False

    if event_type == 'checkout.session.completed':
        handled = await _sync_checkout_session(db, data_obj)
    elif event_type in (
        'customer.subscription.created',
        'customer.subscription.updated',
        'customer.subscription.deleted',
    ):
        handled = await _sync_subscription_object(db, data_obj)
    elif event_type == 'invoice.paid':
        customer_id = data_obj.get('customer')
        tenant = await _tenant_by_stripe_customer(db, customer_id if isinstance(customer_id, str) else None)
        if tenant:
            tenant.subscription_status = 'active'
            handled = True
    else:
        logger.debug('Stripe webhook ignored type=%s', event_type)

    if handled:
        await db.commit()

    return {'handled': handled, 'type': event_type}
