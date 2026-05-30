"""Lite payments — Razorpay or Stripe (customer sees Pay now only)."""

from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.billing.payment_gateways import (
    load_gateway_config,
    payment_enabled,
    preferred_provider,
    razorpay_enabled,
    stripe_enabled,
)
from ...core.billing.razorpay_lite import (
    activate_plan_after_payment,
    create_order,
    plan_amount_paise,
    verify_payment_signature,
)
from ...core.billing.stripe_checkout import create_checkout_session, retrieve_checkout_session
from ...core.database import get_db
from ...core.models import PaymentTransaction, generate_uuid
from ...core.tenant_utils import parse_tenant_uuid
from ..dependencies.access import TenantUser, require_tenant_member
from ..schemas.base import create_response

router = APIRouter(
    prefix='/payments',
    tags=['Payments'],
    dependencies=[Depends(require_tenant_member)],
)


async def _resolve_customer_tenant(current_user: TenantUser, db: AsyncSession):
    from ...core.tenant_utils import resolve_member_tenant_uuid

    tenant_uuid = await resolve_member_tenant_uuid(current_user, db)
    current_user.tenant_id = str(tenant_uuid)
    return tenant_uuid


class CreateRazorpayOrderBody(BaseModel):
    plan_id: str = Field(..., description='plan id from Billing plans list')
    billing_interval: str = 'monthly'


class VerifyRazorpayBody(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: Optional[str] = None
    billing_interval: str = 'monthly'


class StripeCheckoutBody(BaseModel):
    plan_id: str
    billing_interval: str = 'monthly'
    success_url: str
    cancel_url: str


class StripeConfirmBody(BaseModel):
    session_id: str


@router.get('/config')
async def payments_config(_user: TenantUser, db: AsyncSession = Depends(get_db)):
    cfg = await load_gateway_config(db)
    pref = preferred_provider(cfg)
    return create_response(
        {
            'payment_enabled': payment_enabled(cfg),
            'preferred_provider': pref,
            'razorpay_enabled': razorpay_enabled(cfg),
            'stripe_enabled': stripe_enabled(cfg),
            'stripe_publishable_key': cfg.get('stripe_publishable_key') if stripe_enabled(cfg) else None,
            'currency': 'USD',
            'providers': [p for p in ('stripe', 'razorpay') if (p == 'stripe' and stripe_enabled(cfg)) or (p == 'razorpay' and razorpay_enabled(cfg))],
        }
    )


@router.post('/razorpay/create-order')
async def razorpay_create_order(
    body: CreateRazorpayOrderBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    await _resolve_customer_tenant(current_user, db)
    cfg = await load_gateway_config(db)
    if not razorpay_enabled(cfg):
        raise HTTPException(status_code=503, detail='Online payment is not available')

    from ...core.platform.lite_settings import get_setting

    pricing = await get_setting(db, 'pricing')
    try:
        order = create_order(
            tenant_id=current_user.tenant_id,
            plan_id=body.plan_id,
            billing_interval=body.billing_interval,
            user_email=current_user.email,
            pricing=pricing,
            gateway_cfg=cfg,
        )
        tx = PaymentTransaction(
            id=generate_uuid(),
            tenant_id=parse_tenant_uuid(current_user.tenant_id),
            user_id=current_user.user_id,
            provider='razorpay',
            order_id=order['order_id'],
            amount=order['amount'] / 100.0,
            currency=order['currency'],
            plan=order.get('plan'),
            status='created',
            metadata_json={'billing_interval': body.billing_interval},
        )
        db.add(tx)
        await db.commit()
        return create_response(order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail='Payment could not be started') from exc


@router.get('/razorpay/plan-preview')
async def razorpay_plan_preview(
    plan_id: str,
    _user: TenantUser,
    billing_interval: str = 'monthly',
    db: AsyncSession = Depends(get_db),
):
    from ...core.platform.lite_settings import get_setting

    pricing = await get_setting(db, 'pricing')
    try:
        amount = plan_amount_paise(plan_id, billing_interval, pricing=pricing)
        return create_response(
            {
                'plan_id': plan_id,
                'billing_interval': billing_interval,
                'amount_paise': amount,
                'amount_display': f'${amount / 100:,.2f}',
                'currency': 'USD',
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/razorpay/verify')
async def razorpay_verify_payment(
    body: VerifyRazorpayBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    await _resolve_customer_tenant(current_user, db)
    cfg = await load_gateway_config(db)
    if not razorpay_enabled(cfg):
        raise HTTPException(status_code=503, detail='Online payment is not available')

    existing_paid = (
        await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider == 'razorpay',
                PaymentTransaction.payment_id == body.razorpay_payment_id,
            )
        )
    ).scalar_one_or_none()
    if existing_paid and existing_paid.status == 'paid':
        raise HTTPException(status_code=409, detail='This payment was already processed')

    if not verify_payment_signature(
        body.razorpay_order_id,
        body.razorpay_payment_id,
        body.razorpay_signature,
        gateway_cfg=cfg,
    ):
        tx_failed = (
            await db.execute(
                select(PaymentTransaction).where(
                    PaymentTransaction.provider == 'razorpay',
                    PaymentTransaction.order_id == body.razorpay_order_id,
                )
            )
        ).scalar_one_or_none()
        if tx_failed:
            tx_failed.status = 'failed'
            tx_failed.failure_reason = 'signature_verification_failed'
            await db.commit()
        raise HTTPException(status_code=400, detail='Payment verification failed')

    plan_id = body.plan_id or 'plan_pro'
    try:
        await activate_plan_after_payment(
            db,
            tenant_id=parse_tenant_uuid(current_user.tenant_id),
            plan=plan_id,
            billing_interval=body.billing_interval,
            payment_id=body.razorpay_payment_id,
            order_id=body.razorpay_order_id,
            provider='razorpay',
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tx = (
        await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider == 'razorpay',
                PaymentTransaction.order_id == body.razorpay_order_id,
            )
        )
    ).scalar_one_or_none()
    if tx:
        tx.payment_id = body.razorpay_payment_id
        tx.status = 'paid'
        tx.paid_at = datetime.now(timezone.utc)
        tx.plan = plan_id
    else:
        db.add(
            PaymentTransaction(
                id=generate_uuid(),
                tenant_id=parse_tenant_uuid(current_user.tenant_id),
                user_id=current_user.user_id,
                provider='razorpay',
                order_id=body.razorpay_order_id,
                payment_id=body.razorpay_payment_id,
                amount=0,
                currency='USD',
                plan=plan_id,
                status='paid',
                paid_at=datetime.now(timezone.utc),
            )
        )
    await db.commit()

    from ...core.billing.fe_responses import build_subscription_view

    sub = await build_subscription_view(db, parse_tenant_uuid(current_user.tenant_id))
    return create_response(
        {
            'success': True,
            'message': 'Payment verified — plan activated',
            'subscription': sub,
        }
    )


@router.post('/stripe/create-checkout')
async def stripe_create_checkout(
    body: StripeCheckoutBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    await _resolve_customer_tenant(current_user, db)
    cfg = await load_gateway_config(db)
    secret = str(cfg.get('stripe_secret_key') or '').strip()
    if not secret:
        raise HTTPException(status_code=503, detail='Online payment is not available')

    from ...core.platform.lite_settings import get_setting

    pricing = await get_setting(db, 'pricing')
    try:
        session = create_checkout_session(
            secret_key=secret,
            tenant_id=current_user.tenant_id,
            plan_id=body.plan_id,
            billing_interval=body.billing_interval,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            pricing=pricing,
            customer_email=current_user.email,
        )
        amount_cents = plan_amount_paise(body.plan_id, body.billing_interval, pricing=pricing)
        db.add(
            PaymentTransaction(
                id=generate_uuid(),
                tenant_id=parse_tenant_uuid(current_user.tenant_id),
                user_id=current_user.user_id,
                provider='stripe',
                order_id=session['session_id'],
                amount=amount_cents / 100.0,
                currency='USD',
                plan=session.get('plan'),
                status='created',
                metadata_json={'billing_interval': body.billing_interval},
            )
        )
        await db.commit()
        return create_response(session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/stripe/confirm')
async def stripe_confirm_checkout(
    body: StripeConfirmBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    await _resolve_customer_tenant(current_user, db)
    cfg = await load_gateway_config(db)
    secret = str(cfg.get('stripe_secret_key') or '').strip()
    if not secret:
        raise HTTPException(status_code=503, detail='Online payment is not available')

    session = retrieve_checkout_session(secret, body.session_id)
    if str(session.get('payment_status')) != 'paid':
        raise HTTPException(status_code=400, detail='Payment is not completed yet')

    meta = session.get('metadata') or {}
    if str(meta.get('tenant_id')) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail='Payment does not belong to this workspace')

    plan_id = str(meta.get('plan_id') or 'professional')
    billing_interval = str(meta.get('billing_interval') or 'monthly')
    payment_id = str(session.get('payment_intent') or session.get('id') or body.session_id)

    existing = (
        await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider == 'stripe',
                PaymentTransaction.payment_id == payment_id,
            )
        )
    ).scalar_one_or_none()
    if existing and existing.status == 'paid':
        raise HTTPException(status_code=409, detail='This payment was already processed')

    await activate_plan_after_payment(
        db,
        tenant_id=parse_tenant_uuid(current_user.tenant_id),
        plan=plan_id,
        billing_interval=billing_interval,
        payment_id=payment_id,
        order_id=body.session_id,
        provider='stripe',
    )

    tx = (
        await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider == 'stripe',
                PaymentTransaction.order_id == body.session_id,
            )
        )
    ).scalar_one_or_none()
    if tx:
        tx.payment_id = payment_id
        tx.status = 'paid'
        tx.paid_at = datetime.now(timezone.utc)
        tx.plan = plan_id
    else:
        db.add(
            PaymentTransaction(
                id=generate_uuid(),
                tenant_id=parse_tenant_uuid(current_user.tenant_id),
                user_id=current_user.user_id,
                provider='stripe',
                order_id=body.session_id,
                payment_id=payment_id,
                amount=float((session.get('amount_total') or 0)) / 100.0,
                currency=str(session.get('currency') or 'usd').upper(),
                plan=plan_id,
                status='paid',
                paid_at=datetime.now(timezone.utc),
            )
        )
    await db.commit()

    from ...core.billing.fe_responses import build_subscription_view

    sub = await build_subscription_view(db, parse_tenant_uuid(current_user.tenant_id))
    return create_response({'success': True, 'subscription': sub})
