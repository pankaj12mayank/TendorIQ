"""Razorpay checkout for Lite MVP."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from ..config import settings
from .fe_responses import FE_PLAN_TO_API, normalize_plan_id

logger = logging.getLogger(__name__)

try:
    import razorpay

    RAZORPAY_AVAILABLE = True
except ImportError:
    razorpay = None  # type: ignore
    RAZORPAY_AVAILABLE = False

# Amounts in minor units (USD cents).
PLAN_AMOUNT_PAISE: dict[tuple[str, str], int] = {
    ('starter', 'monthly'): 99900,
    ('starter', 'yearly'): 999000,
    ('professional', 'monthly'): 299900,
    ('professional', 'yearly'): 2999000,
    ('enterprise', 'monthly'): 999900,
    ('enterprise', 'yearly'): 9999000,
}


def razorpay_configured() -> bool:
    key = (settings.RAZORPAY_KEY_ID or '').strip()
    secret = (settings.RAZORPAY_KEY_SECRET or '').strip()
    return bool(key and secret and RAZORPAY_AVAILABLE and 'placeholder' not in key.lower())


def get_client():
    if not razorpay_configured():
        raise ValueError('Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env')
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def plan_amount_paise(
    plan_id: str,
    billing_interval: str,
    *,
    pricing: dict | None = None,
) -> int:
    raw = (plan_id or '').strip().lower()
    if raw in ('free', 'plan_free', 'demo'):
        raise ValueError('Free/demo plan does not require payment')
    api_plan = normalize_plan_id(plan_id)
    cycle = 'yearly' if billing_interval in ('yearly', 'annual') else 'monthly'
    from ..platform.lite_settings import pricing_amount_paise

    amount = pricing_amount_paise(plan_id, billing_interval, pricing)
    if amount is None:
        amount = PLAN_AMOUNT_PAISE.get((api_plan, cycle))
    if not amount:
        raise ValueError(f'No price for plan {api_plan} ({cycle})')
    return amount


def create_order(
    *,
    tenant_id: str,
    plan_id: str,
    billing_interval: str,
    user_email: Optional[str] = None,
    pricing: dict | None = None,
    gateway_cfg: dict | None = None,
) -> dict[str, Any]:
    if gateway_cfg:
        from .payment_gateways import razorpay_client

        client = razorpay_client(gateway_cfg)
        key_id = gateway_cfg['razorpay_key_id']
    else:
        client = get_client()
        key_id = settings.RAZORPAY_KEY_ID
    api_plan = normalize_plan_id(plan_id)
    amount = plan_amount_paise(plan_id, billing_interval, pricing=pricing)
    currency = (getattr(settings, 'RAZORPAY_CURRENCY', None) or 'USD').upper()
    receipt = f'tiq_{tenant_id[:8]}_{api_plan}'[:40]

    order = client.order.create(
        {
            'amount': amount,
            'currency': currency,
            'receipt': receipt,
            'notes': {
                'tenant_id': tenant_id,
                'plan': api_plan,
                'billing_interval': billing_interval,
                'email': user_email or '',
            },
        }
    )
    return {
        'order_id': order['id'],
        'amount': amount,
        'currency': currency,
        'key_id': key_id,
        'plan': api_plan,
        'plan_id': plan_id,
        'billing_interval': billing_interval,
    }


def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str,
    gateway_cfg: dict | None = None,
) -> bool:
    if gateway_cfg:
        from .payment_gateways import razorpay_client

        client = razorpay_client(gateway_cfg)
    else:
        client = get_client()
    try:
        client.utility.verify_payment_signature(
            {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            }
        )
        return True
    except Exception as exc:
        logger.warning('Razorpay signature verification failed: %s', exc)
        return False


async def plan_period_days(db, plan_id: str, pricing: dict | None = None) -> int:
    from ..platform.lite_settings import get_setting

    if pricing is None:
        pricing = await get_setting(db, 'pricing')
    api_plan = normalize_plan_id(plan_id)
    for row in (pricing or {}).get('plans') or []:
        if isinstance(row, dict) and normalize_plan_id(str(row.get('id') or '')) == api_plan:
            return max(1, int(row.get('expiry_period_days') or 30))
    return 30


async def activate_plan_after_payment(
    db,
    *,
    tenant_id: UUID,
    plan: str,
    billing_interval: str,
    payment_id: str,
    order_id: str,
    provider: str = 'razorpay',
    period_days: Optional[int] = None,
) -> None:
    from ..models import Tenant, pk_str
    from .subscription_access import (
        apply_plan_period,
        apply_tenant_plan_entitlements,
        sync_subscription_row,
    )

    tenant = await db.get(Tenant, pk_str(tenant_id))
    if not tenant:
        raise ValueError('Tenant not found')

    cycle = 'yearly' if billing_interval in ('yearly', 'annual') else 'monthly'
    tenant.plan = normalize_plan_id(plan)
    tenant.billing_cycle = cycle
    tenant.subscription_status = 'active'
    tenant.subscription_id = payment_id
    apply_tenant_plan_entitlements(tenant, tenant.plan)
    if period_days is None:
        period_days = await plan_period_days(db, plan)
    period_start, period_end = apply_plan_period(
        tenant, billing_cycle=cycle, period_days=period_days
    )

    settings_json = dict(tenant.settings or {})
    payments = list(settings_json.get('payments') or [])
    payments.append(
        {
            'provider': provider,
            'order_id': order_id,
            'payment_id': payment_id,
            'plan': tenant.plan,
            'at': datetime_now_iso(),
        }
    )
    settings_json['payments'] = payments[-20:]
    tenant.settings = settings_json

    await sync_subscription_row(
        db,
        tenant,
        plan=tenant.plan,
        status='active',
        billing_cycle=cycle,
        period_start=period_start,
        period_end=period_end,
    )
    await db.commit()
    await db.refresh(tenant)


def datetime_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
