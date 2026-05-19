"""Billing Plan Limits Enforcement"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Tenant, Subscription, Document, User, Tender, QueueJob

logger = logging.getLogger(__name__)


async def get_usage_for_tenant(tenant_id: UUID) -> dict:
    """Get AI usage for tenant - stub for now"""
    return {'total_tokens': 0}


class PlanLimits:
    PLANS = {
        'starter': {
            'users': 5,
            'documents_per_month': 100,
            'storage_mb': 1024,
            'api_calls_per_month': 1000,
            'ai_tokens_per_month': 50000,
            'tenders': 10,
            'concurrent_ocr': 2,
            'export_per_day': 10,
        },
        'professional': {
            'users': 20,
            'documents_per_month': 500,
            'storage_mb': 10240,
            'api_calls_per_month': 10000,
            'ai_tokens_per_month': 500000,
            'tenders': 50,
            'concurrent_ocr': 5,
            'export_per_day': 50,
        },
        'enterprise': {
            'users': -1,  # unlimited
            'documents_per_month': -1,
            'storage_mb': -1,
            'api_calls_per_month': -1,
            'ai_tokens_per_month': -1,
            'tenders': -1,
            'concurrent_ocr': -1,
            'export_per_day': -1,
        },
    }

    @classmethod
    def get_limits(cls, plan: str) -> dict:
        return cls.PLANS.get(plan, cls.PLANS['starter'])

    @classmethod
    def get_current_usage(cls, db: AsyncSession, tenant_id: UUID, plan: str) -> dict:
        """Get current usage for all limit types"""
        import asyncio
        
        limits = cls.get_limits(plan)
        
        # Count users
        user_count = asyncio.get_event_loop().run_until_complete(
            db.scalar(
                select(func.count(User.id)).where(User.tenant_id == tenant_id)
            ) or 0
        )
        
        # Count documents this month (would need proper date filtering)
        doc_count = asyncio.get_event_loop().run_until_complete(
            db.scalar(
                select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
            ) or 0
        )
        
        # Count tenders
        tender_count = asyncio.get_event_loop().run_until_complete(
            db.scalar(
                select(func.count(Tender.id)).where(Tender.tenant_id == tenant_id)
            ) or 0
        )
        
        # Get AI usage
        ai_usage = asyncio.get_event_loop().run_until_complete(
            get_usage_for_tenant(tenant_id)
        )
        
        return {
            'users': user_count,
            'documents': doc_count,
            'tenders': tender_count,
            'ai_tokens': ai_usage.get('total_tokens', 0),
            'api_calls': 0,  # Would need to track separately
        }


class BillingEnforcer:
    """Enforce plan limits before allowing operations"""

    @staticmethod
    async def check_user_limit(db: AsyncSession, tenant_id: UUID) -> bool:
        """Check if user can be added"""
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        plan = tenant.plan or 'starter'
        limits = PlanLimits.get_limits(plan)
        
        user_count = await db.scalar(
            select(func.count(User.id)).where(User.tenant_id == tenant_id)
        ) or 0
        
        if limits['users'] != -1 and user_count >= limits['users']:
            raise HTTPException(
                status_code=402,
                detail=f"User limit reached. Upgrade to {plan.replace('_', ' ').title()} for more."
            )
        return True

    @staticmethod
    async def check_document_limit(db: AsyncSession, tenant_id: UUID) -> bool:
        """Check if document can be uploaded"""
        tenant = await db.get(Tenant, tenant_id)
        plan = tenant.plan or 'starter'
        limits = PlanLimits.get_limits(plan)
        
        doc_count = await db.scalar(
            select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
        ) or 0
        
        if limits['documents_per_month'] != -1 and doc_count >= limits['documents_per_month']:
            raise HTTPException(
                status_code=402,
                detail=f"Document limit reached for this month. Upgrade plan for more."
            )
        return True

    @staticmethod
    async def check_tender_limit(db: AsyncSession, tenant_id: UUID) -> bool:
        """Check if tender can be created"""
        tenant = await db.get(Tenant, tenant_id)
        plan = tenant.plan or 'starter'
        limits = PlanLimits.get_limits(plan)
        
        tender_count = await db.scalar(
            select(func.count(Tender.id)).where(Tender.tenant_id == tenant_id)
        ) or 0
        
        if limits['tenders'] != -1 and tender_count >= limits['tenders']:
            raise HTTPException(
                status_code=402,
                detail=f"Tender limit reached. Upgrade to create more."
            )
        return True

    @staticmethod
    async def check_ai_tokens(db: AsyncSession, tenant_id: UUID, tokens_to_add: int = 0) -> bool:
        """Check AI token limit"""
        tenant = await db.get(Tenant, tenant_id)
        plan = tenant.plan or 'starter'
        limits = PlanLimits.get_limits(plan)
        
        if limits['ai_tokens_per_month'] == -1:
            return True
        
        current_usage = await get_usage_for_tenant(tenant_id)
        current_tokens = current_usage.get('total_tokens', 0)
        
        if current_tokens + tokens_to_add > limits['ai_tokens_per_month']:
            raise HTTPException(
                status_code=402,
                detail=f"AI token limit reached. Upgrade plan or wait for reset."
            )
        return True

    @staticmethod
    async def check_ocr_concurrency(db: AsyncSession, tenant_id: UUID) -> bool:
        """Check concurrent OCR limit"""
        tenant = await db.get(Tenant, tenant_id)
        plan = tenant.plan or 'starter'
        limits = PlanLimits.get_limits(plan)
        
        active_ocr = await db.scalar(
            select(func.count(QueueJob.id)).where(
                QueueJob.tenant_id == tenant_id,
                QueueJob.job_type == 'ocr',
                QueueJob.status == 'active'
            )
        ) or 0
        
        if limits['concurrent_ocr'] != -1 and active_ocr >= limits['concurrent_ocr']:
            raise HTTPException(
                status_code=429,
                detail=f"Concurrent OCR limit reached. Wait for processing to complete."
            )
        return True

    @staticmethod
    async def check_export_limit(db: AsyncSession, tenant_id: UUID) -> bool:
        """Check daily export limit"""
        tenant = await db.get(Tenant, tenant_id)
        plan = tenant.plan or 'starter'
        limits = PlanLimits.get_limits(plan)
        
        exports_today = await db.scalar(
            select(func.count(QueueJob.id)).where(
                QueueJob.tenant_id == tenant_id,
                QueueJob.job_type == 'export',
            )
        ) or 0
        
        if limits['export_per_day'] != -1 and exports_today >= limits['export_per_day']:
            raise HTTPException(
                status_code=429,
                detail=f"Daily export limit reached. Try again tomorrow."
            )
        return True


class BillingService:
    """Billing and subscription management"""

    @staticmethod
    async def get_subscription(db: AsyncSession, tenant_id: UUID) -> dict:
        """Get subscription details with limits"""
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        plan = tenant.plan or 'starter'
        limits = PlanLimits.get_limits(plan)
        
        # Get current usage
        usage = PlanLimits.get_current_usage(db, tenant_id, plan)
        
        return {
            'plan': plan,
            'status': 'active',
            'billing_cycle': tenant.billing_cycle,
            'limits': {
                'users': {'current': usage['users'], 'max': limits['users']},
                'documents': {'current': usage['documents'], 'max': limits['documents_per_month']},
                'tenders': {'current': usage['tenders'], 'max': limits['tenders']},
                'ai_tokens': {'current': usage['ai_tokens'], 'max': limits['ai_tokens_per_month']},
            }
        }

    @staticmethod
    async def check_all_limits(db: AsyncSession, tenant_id: UUID, operation: str) -> bool:
        """Check relevant limit before operation"""
        enforcer = BillingEnforcer
        
        checks = {
            'create_user': enforcer.check_user_limit,
            'upload_document': enforcer.check_document_limit,
            'create_tender': enforcer.check_tender_limit,
            'ai_request': enforcer.check_ai_tokens,
            'ocr_submit': enforcer.check_ocr_concurrency,
            'export': enforcer.check_export_limit,
        }
        
        check_func = checks.get(operation)
        if check_func:
            return await check_func(db, tenant_id)
        return True


__all__ = ['PlanLimits', 'BillingEnforcer', 'BillingService']