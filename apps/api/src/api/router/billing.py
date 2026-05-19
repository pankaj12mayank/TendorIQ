"""Billing API - Plan Limits and Subscription Management"""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ...core.models import Tenant
from ...core.database import get_db
from ...dependencies.auth import get_current_user
from ...core.auth import AuthContext
from ...core.billing import BillingService, PlanLimits

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/billing', tags=['Billing'])


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    billing_cycle: str
    limits: dict


class UsageResponse(BaseModel):
    users: dict
    documents: dict
    tenders: dict
    ai_tokens: dict


class PlanUpgradeRequest(BaseModel):
    plan: str
    billing_cycle: str = 'monthly'


@router.get('/subscription', response_model=SubscriptionResponse)
async def get_subscription(
    current_user: AuthContext = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current subscription and limits"""
    tenant_id = current_user.tenant_id
    
    return await BillingService.get_subscription(db, tenant_id)


@router.get('/usage', response_model=UsageResponse)
async def get_usage(
    current_user: AuthContext = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current usage statistics"""
    tenant_id = current_user.tenant_id
    tenant = await db.get(Tenant, tenant_id)
    plan = tenant.plan or 'starter'
    
    usage = PlanLimits.get_current_usage(db, tenant_id, plan)
    limits = PlanLimits.get_limits(plan)
    
    return UsageResponse(
        users={'current': usage['users'], 'max': limits['users']},
        documents={'current': usage['documents'], 'max': limits['documents_per_month']},
        tenders={'current': usage['tenders'], 'max': limits['tenders']},
        ai_tokens={'current': usage['ai_tokens'], 'max': limits['ai_tokens_per_month']},
    )


@router.get('/plans')
async def get_plans():
    """Get available plans"""
    return {
        'plans': [
            {
                'id': 'starter',
                'name': 'Starter',
                'price': 29,
                'interval': 'monthly',
                'limits': PlanLimits.PLANS['starter'],
            },
            {
                'id': 'professional',
                'name': 'Professional',
                'price': 99,
                'interval': 'monthly',
                'limits': PlanLimits.PLANS['professional'],
            },
            {
                'id': 'enterprise',
                'name': 'Enterprise',
                'price': 299,
                'interval': 'monthly',
                'limits': PlanLimits.PLANS['enterprise'],
            },
        ]
    }


@router.post('/upgrade')
async def upgrade_plan(
    request: PlanUpgradeRequest,
    current_user: AuthContext = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upgrade subscription plan"""
    tenant_id = current_user.tenant_id
    tenant = await db.get(Tenant, tenant_id)
    
    # In production, this would:
    # 1. Call Stripe API to update subscription
    # 2. Handle payment
    # 3. Update tenant plan
    
    tenant.plan = request.plan
    tenant.billing_cycle = request.billing_cycle
    await db.commit()
    
    logger.info(f"Tenant {tenant_id} upgraded to {request.plan}")
    
    return {'success': True, 'plan': request.plan, 'message': 'Plan upgraded successfully'}


@router.post('/check-limit/{operation}')
async def check_limit(
    operation: str,
    current_user: AuthContext = Depends(get_current_user),
    db=Depends(get_db),
):
    """Check if operation is allowed under current plan"""
    tenant_id = current_user.tenant_id
    
    allowed = await BillingService.check_all_limits(db, tenant_id, operation)
    
    return {'allowed': allowed, 'operation': operation}


router_check = router  # Alias for cleaner imports