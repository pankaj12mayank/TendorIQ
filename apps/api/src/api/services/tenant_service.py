"""Tenant Service - Core Tenant Operations"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import Tenant, Membership, User
from ...core.logging import get_logger

logger = get_logger('tenant_service')


class TenantService:
    """Service for tenant operations"""

    @staticmethod
    async def get_tenant_by_id(db: AsyncSession, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        result = await db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_tenant(
        db: AsyncSession,
        name: str,
        slug: str,
        owner_id: UUID,
        **kwargs
    ) -> Tenant:
        """Create new tenant with owner"""
        tenant = Tenant(
            name=name,
            slug=slug,
            **kwargs
        )
        db.add(tenant)
        await db.flush()

        membership = Membership(
            user_id=owner_id,
            tenant_id=tenant.id,
            role='owner',
            status='active'
        )
        db.add(membership)
        await db.commit()
        await db.refresh(tenant)

        logger.info(f'Tenant created: {tenant.id} by user {owner_id}')
        return tenant

    @staticmethod
    async def update_tenant(
        db: AsyncSession,
        tenant_id: UUID,
        **updates
    ) -> Optional[Tenant]:
        """Update tenant details"""
        tenant = await TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None

        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def deactivate_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
        """Deactivate tenant"""
        tenant = await TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return False

        tenant.status = 'inactive'
        await db.commit()
        return True

    @staticmethod
    async def check_tenant_quota(
        db: AsyncSession,
        tenant_id: UUID,
        resource: str
    ) -> tuple[bool, Optional[str]]:
        """Check if tenant has quota for resource"""
        tenant = await TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return False, 'Tenant not found'

        if tenant.status != 'active':
            return False, 'Tenant is not active'

        if resource == 'users':
            if tenant.used_users >= tenant.quota_users:
                return False, 'User quota exceeded'
        elif resource == 'documents':
            if tenant.used_documents >= tenant.quota_documents:
                return False, 'Document quota exceeded'
        elif resource == 'storage':
            if tenant.used_storage_mb >= tenant.quota_storage_mb:
                return False, 'Storage quota exceeded'

        return True, None


tenant_service = TenantService()