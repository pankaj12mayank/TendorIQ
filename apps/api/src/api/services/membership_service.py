"""Membership Service - User-Tenant Relationship Management"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import Membership, User, Tenant
from ...core.logging import get_logger

logger = get_logger('membership_service')


class MembershipService:
    """Service for membership operations"""

    @staticmethod
    async def get_membership(
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> Optional[Membership]:
        """Get user's membership for a specific tenant"""
        result = await db.execute(
            select(Membership).where(
                and_(
                    Membership.user_id == user_id,
                    Membership.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_memberships(
        db: AsyncSession,
        user_id: UUID
    ) -> list[Membership]:
        """Get all memberships for a user"""
        result = await db.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .where(Membership.status == 'active')
            .order_by(Membership.joined_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_tenant_members(
        db: AsyncSession,
        tenant_id: UUID,
        status: Optional[str] = None
    ) -> list[Membership]:
        """Get all members of a tenant"""
        query = select(Membership).where(Membership.tenant_id == tenant_id)
        if status:
            query = query.where(Membership.status == status)
        result = await db.execute(query.order_by(Membership.joined_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_active_tenant_ids(db: AsyncSession, user_id: UUID) -> list[UUID]:
        """Get all active tenant IDs for a user"""
        result = await db.execute(
            select(Membership.tenant_id)
            .where(
                and_(
                    Membership.user_id == user_id,
                    Membership.status == 'active'
                )
            )
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def invite_member(
        db: AsyncSession,
        tenant_id: UUID,
        email: str,
        role: str,
        invited_by_id: UUID
    ) -> Membership:
        """Invite a new member to tenant"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user:
            existing = await MembershipService.get_membership(db, user.id, tenant_id)
            if existing:
                if existing.status == 'active':
                    raise ValueError('User is already a member')
                existing.status = 'pending'
                existing.role = role
                await db.commit()
                await db.refresh(existing)
                return existing

            membership = Membership(
                user_id=user.id,
                tenant_id=tenant_id,
                role=role,
                status='pending',
                invited_by_id=invited_by_id
            )
        else:
            membership = Membership(
                user_id=None,
                tenant_id=tenant_id,
                role=role,
                status='pending',
                invited_by_id=invited_by_id
            )

        db.add(membership)
        await db.commit()
        await db.refresh(membership)

        logger.info(f'User invited to tenant: {email} as {role}')
        return membership

    @staticmethod
    async def accept_invitation(
        db: AsyncSession,
        membership_id: UUID,
        user_id: UUID
    ) -> Membership:
        """Accept invitation and activate membership"""
        result = await db.execute(
            select(Membership).where(Membership.id == membership_id)
        )
        membership = result.scalar_one_or_none()

        if not membership:
            raise ValueError('Invitation not found')

        if membership.user_id != user_id:
            raise ValueError('Invalid user')

        if membership.status != 'pending':
            raise ValueError('Invitation already processed')

        membership.status = 'active'
        membership.joined_at = datetime.utcnow()

        await db.commit()
        await db.refresh(membership)

        logger.info(f'Membership activated: {membership_id}')
        return membership

    @staticmethod
    async def update_role(
        db: AsyncSession,
        membership_id: UUID,
        new_role: str,
        updated_by_id: UUID
    ) -> Membership:
        """Update member's role"""
        result = await db.execute(
            select(Membership).where(Membership.id == membership_id)
        )
        membership = result.scalar_one_or_none()

        if not membership:
            raise ValueError('Membership not found')

        old_role = membership.role
        membership.role = new_role

        await db.commit()
        await db.refresh(membership)

        logger.info(
            f'Role updated for membership {membership_id}: {old_role} -> {new_role}'
        )
        return membership

    @staticmethod
    async def suspend_member(
        db: AsyncSession,
        membership_id: UUID,
        suspended_by_id: UUID
    ) -> Membership:
        """Suspend a member"""
        result = await db.execute(
            select(Membership).where(Membership.id == membership_id)
        )
        membership = result.scalar_one_or_none()

        if not membership:
            raise ValueError('Membership not found')

        membership.status = 'suspended'
        await db.commit()
        await db.refresh(membership)

        logger.info(f'Member suspended: {membership_id}')
        return membership

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        membership_id: UUID,
        removed_by_id: UUID
    ) -> bool:
        """Remove member from tenant"""
        result = await db.execute(
            select(Membership).where(Membership.id == membership_id)
        )
        membership = result.scalar_one_or_none()

        if not membership:
            return False

        if membership.role == 'owner':
            raise ValueError('Cannot remove owner')

        await db.delete(membership)
        await db.commit()

        logger.info(f'Member removed: {membership_id}')
        return True

    @staticmethod
    async def switch_tenant(
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> tuple[Optional[Membership], Optional[Tenant]]:
        """Switch user's active tenant"""
        membership = await MembershipService.get_membership(db, user_id, tenant_id)

        if not membership:
            return None, None

        if membership.status != 'active':
            return None, None

        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant or tenant.status != 'active':
            return None, None

        return membership, tenant


membership_service = MembershipService()