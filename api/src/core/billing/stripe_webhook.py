"""Apply Stripe webhook events to tenant subscription state."""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone
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
    'unpaid': 'past_due',
    'incomplete': 'past_due',
    'incomplete_expired': 'canceled',
}

# Track processed event IDs to guarantee idempotency.
_PROCESSED_EVENTS: set[str] = set()


def verify_stripe_signature(
    payload: bytes,
    sig_header: str,
    webhook_secret: str,
    *,
    tolerance_seconds: int = 300,
) -> bool:
    """Verify Stripe webhook signature using HMAC-SHA256."""
    if not webhook_secret or not sig_header:
        return False
    try:
        parts = {}
        for item in sig_header.split(','):
            kv = item.strip().split('=', 1)
            if len(kv) == 2:
                parts[kv[0]] = kv[1]
        timestamp = parts.get('t')
        signature = parts.get('v1')
        if not timestamp or not signature:
            return False
        signed_payload = f'{timestamp}.{payload.decode("utf-8")}'.encode('utf-8')
        expected = hmac.new(
            webhook_secret.encode('utf-8'),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return False
        import time
        if abs(time.time() - int(timestamp)) > tolerance_seconds:
            logger.warning('Stripe webhook signature timestamp is too old')
            return False
        return True
    except Exception as exc:
        logger.warning('Stripe webhook signature verification error: %s', exc)
        return False


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
    current_period_end: Optional[datetime] = None,
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
    sub_status = norm_status if norm_status in ('active', 'trialing', 'past_due', 'cancelled', 'unpaid') else 'active'
    if existing:
        existing.plan = tenant.plan
        existing.status = sub_status
        if stripe_subscription_id:
            existing.stripe_subscription_id = stripe_subscription_id
        if stripe_customer_id:
            existing.stripe_customer_id = stripe_customer_id
        existing.billing_cycle = billing_cycle
        if current_period_end:
            existing.current_period_end = current_period_end
    else:
        sub = Subscription(
            tenant_id=tenant.id,
            plan=tenant.plan,
            status=sub_status,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            billing_cycle=billing_cycle,
            amount=0.0,
        )
        if current_period_end:
            sub.current_period_end = current_period_end
        db.add(sub)

    if current_period_end:
        from .subscription_access import apply_plan_period
        settings = dict(tenant.settings or {})
        settings['plan_period_end'] = current_period_end.isoformat()
        tenant.settings = settings


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
        billing_interval='monthly',
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

    period_end_raw = sub.get('current_period_end')
    current_period_end: Optional[datetime] = None
    if period_end_raw and isinstance(period_end_raw, (int, float)):
        current_period_end = datetime.fromtimestamp(period_end_raw, tz=timezone.utc)

    await _upsert_subscription_row(
        db,
        tenant,
        plan=plan,
        status=status,
        stripe_subscription_id=stripe_sub_id if isinstance(stripe_sub_id, str) else None,
        stripe_customer_id=customer_id if isinstance(customer_id, str) else None,
        current_period_end=current_period_end,
    )
    return True


async def _handle_invoice_event(db: AsyncSession, data_obj: dict[str, Any], event_type: str) -> bool:
    """Handle invoice.paid and invoice.payment_failed."""
    customer_id = data_obj.get('customer')
    tenant = await _tenant_by_stripe_customer(db, customer_id if isinstance(customer_id, str) else None)
    if not tenant:
        logger.warning('Stripe invoice event: tenant not resolved customer=%s', customer_id)
        return False

    if event_type == 'invoice.paid':
        tenant.subscription_status = 'active'
        logger.info('Stripe invoice.paid: tenant %s set to active', tenant.id)
    elif event_type == 'invoice.payment_failed':
        tenant.subscription_status = 'past_due'
        logger.warning('Stripe invoice.payment_failed: tenant %s set to past_due', tenant.id)

    subscription_id = data_obj.get('subscription')
    if subscription_id and isinstance(subscription_id, str):
        tenant.subscription_id = subscription_id

    billing_reason = data_obj.get('billing_reason')
    if billing_reason == 'subscription_cycle':
        period_end_raw = data_obj.get('period_end') or data_obj.get('lines', {}).get('data', [{}])[0].get('period', {}).get('end')
        if period_end_raw and isinstance(period_end_raw, (int, float)):
            pd = datetime.fromtimestamp(period_end_raw, tz=timezone.utc)
            from .subscription_access import apply_plan_period
            settings = dict(tenant.settings or {})
            settings['plan_period_end'] = pd.isoformat()
            tenant.settings = settings
            logger.info('Stripe invoice: tenant %s period_end updated to %s', tenant.id, pd.isoformat())

    return True


async def apply_stripe_webhook_event(
    db: AsyncSession,
    event: dict[str, Any],
    *,
    event_id: Optional[str] = None,
) -> dict[str, Any]:
    """Persist subscription changes from a verified Stripe event payload."""
    event_id = event_id or str(event.get('id', ''))
    if event_id and event_id in _PROCESSED_EVENTS:
        logger.info('Stripe webhook duplicate event skipped id=%s', event_id)
        return {'handled': False, 'type': str(event.get('type', '')), 'duplicate': True}

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
    elif event_type in ('invoice.paid', 'invoice.payment_failed'):
        handled = await _handle_invoice_event(db, data_obj, event_type)
    else:
        logger.debug('Stripe webhook ignored type=%s', event_type)

    if handled:
        await db.commit()
        if event_id:
            _PROCESSED_EVENTS.add(event_id)

    return {'handled': handled, 'type': event_type, 'duplicate': False}
