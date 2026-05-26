"""Lite payments — Razorpay checkout + verify."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.billing.razorpay_lite import (
    activate_plan_after_payment,
    create_order,
    plan_amount_paise,
    razorpay_configured,
    verify_payment_signature,
)
from ...core.database import get_db
from ...core.tenant_utils import parse_tenant_uuid
from ..dependencies.access import TenantUser, require_tenant_member
from ..schemas.base import create_response

router = APIRouter(
    prefix='/payments',
    tags=['Payments'],
    dependencies=[Depends(require_tenant_member)],
)


class CreateRazorpayOrderBody(BaseModel):
    plan_id: str = Field(..., description='plan_free | plan_pro | starter | professional')
    billing_interval: str = 'monthly'


class VerifyRazorpayBody(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: Optional[str] = None
    billing_interval: str = 'monthly'


@router.get('/config')
async def payments_config(_user: TenantUser):
    from ...core.config import settings

    return create_response(
        {
            'razorpay_enabled': razorpay_configured(),
            'razorpay_key_id': settings.RAZORPAY_KEY_ID if razorpay_configured() else None,
            'currency': 'INR',
            'providers': ['razorpay'] if razorpay_configured() else [],
        }
    )


@router.post('/razorpay/create-order')
async def razorpay_create_order(
    body: CreateRazorpayOrderBody,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Workspace context required')
    if not razorpay_configured():
        raise HTTPException(
            status_code=503,
            detail='Razorpay not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env',
        )
    from ...core.platform.lite_settings import get_setting

    pricing = await get_setting(db, 'pricing')
    try:
        order = create_order(
            tenant_id=current_user.tenant_id,
            plan_id=body.plan_id,
            billing_interval=body.billing_interval,
            user_email=current_user.email,
            pricing=pricing,
        )
        return create_response(order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
                'amount_display': f'₹{amount / 100:,.2f}',
                'currency': 'INR',
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
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Workspace context required')
    if not razorpay_configured():
        raise HTTPException(status_code=503, detail='Razorpay not configured')

    if not verify_payment_signature(
        body.razorpay_order_id,
        body.razorpay_payment_id,
        body.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail='Invalid payment signature')

    plan_id = body.plan_id or 'plan_pro'
    try:
        await activate_plan_after_payment(
            db,
            tenant_id=parse_tenant_uuid(current_user.tenant_id),
            plan=plan_id,
            billing_interval=body.billing_interval,
            payment_id=body.razorpay_payment_id,
            order_id=body.razorpay_order_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    from ...core.billing.fe_responses import build_subscription_view

    sub = await build_subscription_view(db, parse_tenant_uuid(current_user.tenant_id))
    return create_response(
        {
            'success': True,
            'message': 'Payment verified — plan upgraded',
            'subscription': sub,
        }
    )
