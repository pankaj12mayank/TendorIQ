"""Tenant Query Helpers - Tenant-Aware Database Operations"""

from typing import Optional, Any
from uuid import UUID

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Tenant,
    User,
    Membership,
    Tender,
    Document,
    Proposal,
    UsageLog,
    Subscription,
    AnalysisResult,
    TenantMixin,
)
from .logging import get_logger

logger = get_logger('tenant_queries')


class TenantQueryHelper:
    """Helper class for tenant-scoped queries"""

    @staticmethod
    def apply_tenant_filter(query, tenant_id: UUID):
        """Apply tenant filter to any query"""
        return query.where(TenantMixin.tenant_id == tenant_id)

    @staticmethod
    async def get_tenant_with_members(
        db: AsyncSession,
        tenant_id: UUID
    ) -> Optional[Tenant]:
        """Get tenant with all members"""
        result = await db.execute(
            select(Tenant)
            .options(selectinload(Tenant.memberships).selectinload(Membership.user))
            .where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_tenants(
        db: AsyncSession,
        user_id: UUID,
        status: Optional[str] = 'active'
    ) -> list[Tenant]:
        """Get all tenants a user belongs to"""
        query = (
            select(Tenant)
            .join(Membership)
            .where(Membership.user_id == user_id)
        )
        if status:
            query = query.where(Membership.status == status)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def count_tenant_tenders(
        db: AsyncSession,
        tenant_id: UUID,
        status: Optional[str] = None
    ) -> int:
        """Count tenders for tenant"""
        query = select(func.count(Tender.id)).where(Tender.tenant_id == tenant_id)
        if status:
            query = query.where(Tender.status == status)
        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def count_tenant_documents(
        db: AsyncSession,
        tenant_id: UUID
    ) -> int:
        """Count documents for tenant"""
        query = select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def get_tenant_usage_logs(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 100
    ) -> list[UsageLog]:
        """Get usage logs for tenant"""
        query = select(UsageLog).where(UsageLog.tenant_id == tenant_id)
        
        if user_id:
            query = query.where(UsageLog.user_id == user_id)
        
        query = query.order_by(UsageLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_tenant_subscriptions(
        db: AsyncSession,
        tenant_id: UUID
    ) -> list[Subscription]:
        """Get subscriptions for tenant"""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def verify_tenant_access(
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> tuple[bool, Optional[str]]:
        """Verify user has access to tenant"""
        membership = await db.execute(
            select(Membership).where(
                and_(
                    Membership.user_id == user_id,
                    Membership.tenant_id == tenant_id
                )
            )
        )
        membership = membership.scalar_one_or_none()

        if not membership:
            return False, 'Not a member of this organization'

        if membership.status != 'active':
            return False, 'Membership is not active'

        tenant = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant.scalar_one_or_none()

        if not tenant:
            return False, 'Organization not found'

        if tenant.status != 'active':
            return False, 'Organization is not active'

        return True, None


class TenantSecurity:
    """Security helpers for tenant operations"""

    @staticmethod
    async def verify_resource_ownership(
        db: AsyncSession,
        resource: Any,
        tenant_id: UUID
    ) -> bool:
        """Verify resource belongs to tenant"""
        if hasattr(resource, 'tenant_id'):
            return str(resource.tenant_id) == str(tenant_id)
        return False

    @staticmethod
    def sanitize_tenant_input(tenant_id: str) -> Optional[UUID]:
        """Sanitize and validate tenant ID input"""
        try:
            return UUID(tenant_id)
        except (ValueError, TypeError):
            return None


tenant_query = TenantQueryHelper()
tenant_security = TenantSecurity()