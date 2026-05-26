"""Billing API — subscriptions, usage quotas, and plan changes."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...core.billing import BillingService, PlanLimits
from ...core.billing.fe_responses import (
    build_plans_for_fe,
    build_quota_list,
    build_subscription_view,
    build_usage_summary,
    fe_billing_interval,
    get_ai_token_usage,
    normalize_billing_cycle,
    normalize_plan_id,
)
from ...core.database import get_db
from ...core.models import Tenant
from ...core.tenant_utils import parse_tenant_uuid
from ..dependencies.access import TenantUser, require_tenant_member
from ..schemas.base import create_response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import AuthContext

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/billing',
    tags=['Billing'],
    dependencies=[Depends(require_tenant_member)],
)


class PlanUpgradeRequest(BaseModel):
    plan: Optional[str] = None
    plan_id: Optional[str] = None
    billing_cycle: str = 'monthly'
    billing_interval: Optional[str] = None


class SubscriptionChangeRequest(BaseModel):
    plan_id: str
    billing_interval: str = 'monthly'


class CancelSubscriptionRequest(BaseModel):
    reason: Optional[str] = None


class UsageTrackRequest(BaseModel):
    feature_key: str
    quantity: int = Field(1, ge=1)
    metadata: dict = Field(default_factory=dict)


def _require_tenant_uuid(auth: AuthContext) -> UUID:
    if not auth.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')
    return parse_tenant_uuid(auth.tenant_id)


@router.get('/subscription')
async def get_subscription(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = _require_tenant_uuid(current_user)
    return create_response(await build_subscription_view(db, tenant_id))


@router.get('/usage')
async def get_usage(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    """Legacy usage buckets (users, documents, tenders, ai_tokens)."""
    tenant_id = _require_tenant_uuid(current_user)
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail='Tenant not found')

    plan = tenant.plan or 'starter'
    usage = await PlanLimits.get_current_usage(db, tenant_id, plan)
    usage['ai_tokens'] = await get_ai_token_usage(db, tenant_id)
    limits = PlanLimits.get_limits(plan)

    return {
        'users': {'current': usage['users'], 'max': limits['users']},
        'documents': {'current': usage['documents'], 'max': limits['documents_per_month']},
        'tenders': {'current': usage['tenders'], 'max': limits['tenders']},
        'ai_tokens': {'current': usage['ai_tokens'], 'max': limits['ai_tokens_per_month']},
    }


@router.get('/demo-status')
async def get_demo_status(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    """Demo quota usage for Lite MVP."""
    from ...core.billing.lite_usage import build_demo_status

    tenant_id = _require_tenant_uuid(current_user)
    return create_response(await build_demo_status(db, tenant_id))


@router.get('/quota')
async def get_quota(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = _require_tenant_uuid(current_user)
    quotas = await build_quota_list(db, tenant_id)
    return create_response({'quotas': quotas, 'quota': quotas})


@router.get('/usage/summary')
async def get_usage_summary(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = _require_tenant_uuid(current_user)
    return create_response(await build_usage_summary(db, tenant_id))


@router.get('/plans')
async def get_plans():
    plans = build_plans_for_fe()
    body = create_response(plans)
    body['plans'] = plans
    return body


@router.post('/upgrade')
async def upgrade_plan(
    request: PlanUpgradeRequest,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = _require_tenant_uuid(current_user)
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail='Tenant not found')

    plan_raw = request.plan_id or request.plan or 'starter'
    plan = normalize_plan_id(plan_raw)
    cycle = normalize_billing_cycle(request.billing_interval or request.billing_cycle)

    if plan not in PlanLimits.PLANS:
        raise HTTPException(status_code=400, detail='Invalid plan')

    tenant.plan = plan
    tenant.billing_cycle = cycle
    tenant.subscription_status = 'active'
    await db.commit()

    logger.info('Tenant %s upgraded to %s (%s)', tenant_id, plan, cycle)
    return {
        'success': True,
        'plan': plan,
        'message': 'Plan upgraded successfully',
        'subscription': await build_subscription_view(db, tenant_id),
    }


@router.post('/subscription/change')
async def change_subscription(
    request: SubscriptionChangeRequest,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    result = await upgrade_plan(
        PlanUpgradeRequest(plan_id=request.plan_id, billing_interval=request.billing_interval),
        current_user,
        db,
    )
    return {
        'success': True,
        'prorationAmount': 0,
        'immediateCharge': False,
        'nextBillingDate': (await build_subscription_view(db, _require_tenant_uuid(current_user)))[
            'currentPeriodEnd'
        ],
        'subscription': result.get('subscription'),
    }


@router.post('/subscription/cancel')
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = _require_tenant_uuid(current_user)
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail='Tenant not found')

    tenant.subscription_status = 'canceled'
    await db.commit()
    return {'success': True, 'subscription': await build_subscription_view(db, tenant_id)}


@router.post('/subscription/reactivate')
async def reactivate_subscription(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = _require_tenant_uuid(current_user)
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail='Tenant not found')

    tenant.subscription_status = 'active'
    await db.commit()
    return {'success': True, 'subscription': await build_subscription_view(db, tenant_id)}


@router.get('/invoices')
async def list_invoices(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    body = create_response([])
    body['invoices'] = []
    return body


@router.get('/payment-methods')
async def list_payment_methods(
    current_user: TenantUser,
):
    body = create_response([])
    body['payment_methods'] = []
    return body


@router.post('/payment-methods')
async def add_payment_method(
    body: dict,
    current_user: TenantUser,
):
    return {
        'id': 'pm_local',
        'userId': current_user.user_id,
        'stripePaymentMethodId': 'pm_local',
        'type': 'card',
        'brand': 'visa',
        'last4': '4242',
        'isDefault': True,
        'isActive': True,
        'createdAt': '',
    }


@router.patch('/payment-methods/{method_id}')
async def update_payment_method(
    method_id: str,
    body: dict,
    current_user: TenantUser,
):
    return {'success': True, 'id': method_id, 'is_default': body.get('is_default', False)}


@router.delete('/payment-methods/{method_id}', status_code=204)
async def delete_payment_method(
    method_id: str,
    current_user: TenantUser,
):
    return None


@router.post('/usage/track')
async def track_usage(
    body: UsageTrackRequest,
    current_user: TenantUser,
):
    return {'success': True, 'feature_key': body.feature_key, 'quantity': body.quantity}


@router.post('/check-limit/{operation}')
async def check_limit(
    operation: str,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = _require_tenant_uuid(current_user)
    allowed = await BillingService.check_all_limits(db, tenant_id, operation)
    return {'allowed': allowed, 'operation': operation}
