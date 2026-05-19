"""Admin Service Management - Check user roles and service purchases"""

import logging
from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.models import Tenant, User, Subscription, Membership
from ...core.database import get_db
from ..dependencies.auth import get_current_user
from ...core.auth import AuthContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/admin', tags=['Admin'])


class UserRoleResponse(BaseModel):
    user_id: str
    email: str
    role: str
    membership_role: Optional[str]
    tenant_id: Optional[str]
    plan: str
    is_admin: bool


class ServicePurchaseRequest(BaseModel):
    service_name: str
    plan: str


class ServicePurchaseResponse(BaseModel):
    success: bool
    message: str
    purchase_id: Optional[str]
    services: list


@router.get('/whoami', response_model=UserRoleResponse)
async def whoami(
    current_user: AuthContext = Depends(get_current_user),
):
    """Check current user's role and permissions"""
    
    is_admin = current_user.role in ['super_admin', 'owner', 'admin', 'tenant_admin']
    
    return UserRoleResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role or 'user',
        membership_role=current_user.membership_role,
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        plan='starter',  # Will be fetched from tenant
        is_admin=is_admin,
    )


@router.get('/users')
async def list_tenant_users(
    current_user: AuthContext = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all users in the current tenant (admin only)"""
    
    # Check if admin
    if current_user.role not in ['super_admin', 'owner', 'admin', 'tenant_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="No tenant context"
        )
    
    # Get all members in tenant
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    stmt = select(Membership).where(
        Membership.tenant_id == current_user.tenant_id
    ).options(selectinload(Membership.user))
    
    result = await db.execute(stmt)
    members = result.scalars().all()
    
    users = []
    for member in members:
        users.append({
            'user_id': str(member.user_id),
            'email': member.user.email if member.user else 'Unknown',
            'membership_role': member.role,
            'joined_at': member.created_at.isoformat() if member.created_at else None,
        })
    
    return {
        'users': users,
        'total': len(users),
    }


@router.get('/services')
async def get_available_services(
    current_user: AuthContext = Depends(get_current_user),
):
    """Get all available services for purchase"""
    
    return {
        'services': [
            {
                'id': 'ai_analysis',
                'name': 'AI Analysis',
                'description': 'Advanced AI-powered tender analysis',
                'plans': {
                    'starter': {'price': 0, 'limit': '100/month'},
                    'professional': {'price': 49, 'limit': '1000/month'},
                    'enterprise': {'price': 199, 'limit': 'unlimited'},
                },
            },
            {
                'id': 'risk_detection',
                'name': 'Risk Detection',
                'description': 'Automated risk and compliance detection',
                'plans': {
                    'starter': {'price': 0, 'limit': '50/month'},
                    'professional': {'price': 29, 'limit': '500/month'},
                    'enterprise': {'price': 99, 'limit': 'unlimited'},
                },
            },
            {
                'id': 'proposal_generator',
                'name': 'Proposal Generator',
                'description': 'AI-assisted proposal creation',
                'plans': {
                    'starter': {'price': 0, 'limit': '10/month'},
                    'professional': {'price': 59, 'limit': '100/month'},
                    'enterprise': {'price': 199, 'limit': 'unlimited'},
                },
            },
            {
                'id': 'ocr_processing',
                'name': 'OCR Processing',
                'description': 'Document OCR and text extraction',
                'plans': {
                    'starter': {'price': 0, 'limit': '100 pages'},
                    'professional': {'price': 19, 'limit': '1000 pages'},
                    'enterprise': {'price': 49, 'limit': 'unlimited'},
                },
            },
        ]
    }


@router.post('/purchase')
async def purchase_service(
    request: ServicePurchaseRequest,
    current_user: AuthContext = Depends(get_current_user),
    db=Depends(get_db),
):
    """Purchase a service for the tenant"""
    
    # Check if admin
    if current_user.role not in ['super_admin', 'owner', 'admin', 'tenant_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin access required to purchase services"
        )
    
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="No tenant context"
        )
    
    # In production, this would:
    # 1. Create a Stripe checkout session
    # 2. Process payment
    # 3. Update tenant subscription
    
    purchase_id = f"purchase_{datetime.utcnow().timestamp()}"
    
    logger.info(f"Service purchase: {current_user.tenant_id} - {request.service_name} - {request.plan}")
    
    return ServicePurchaseResponse(
        success=True,
        message=f"Successfully purchased {request.service_name} ({request.plan})",
        purchase_id=purchase_id,
        services=[
            {
                'service': request.service_name,
                'plan': request.plan,
                'status': 'active',
                'purchased_at': datetime.utcnow().isoformat(),
            }
        ],
    )


@router.get('/subscription')
async def get_tenant_subscription(
    current_user: AuthContext = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get tenant subscription and services"""
    
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="No tenant context"
        )
    
    from sqlalchemy import select
    
    tenant = await db.get(Tenant, current_user.tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    return {
        'tenant_id': str(tenant.id),
        'tenant_name': tenant.name,
        'plan': tenant.plan or 'starter',
        'billing_cycle': tenant.billing_cycle or 'monthly',
        'subscription_status': 'active',
        'services': [
            {'service': 'ai_analysis', 'status': 'active'},
            {'service': 'risk_detection', 'status': 'active'},
            {'service': 'proposal_generator', 'status': 'active'},
            {'service': 'ocr_processing', 'status': 'active'},
        ],
    }


router_check = router