"""Bootstrap demo tenant user for development login."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .logging import get_logger
from .models import Membership, Tenant, User, generate_uuid
from .roles import coerce_membership_role, PLATFORM_ROLE_SUPER_ADMIN

logger = get_logger('account_bootstrap')


async def ensure_demo_account(
    db: AsyncSession,
    *,
    email: str,
    name: str,
    membership_role: str,
) -> tuple[str, str, str]:
    """Ensure demo tenant, user, and active membership exist.

    Returns:
        (user_id, tenant_id, membership_role)
    """
    role = coerce_membership_role(membership_role, default='admin')
    slug = (settings.DEMO_TENANT_SLUG or 'demo').strip().lower()

    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == slug))
    ).scalar_one_or_none()
    if not tenant:
        tenant = Tenant(
            id=generate_uuid(),
            name=settings.DEMO_TENANT_NAME or 'Demo Organization',
            slug=slug,
            plan='professional',
            status='active',
        )
        db.add(tenant)
        await db.flush()
        logger.info('Created demo tenant slug=%s id=%s', slug, tenant.id)

    normalized_email = email.strip().lower()
    user = (
        await db.execute(select(User).where(User.email == normalized_email))
    ).scalar_one_or_none()
    if not user:
        user = User(
            id=generate_uuid(),
            email=normalized_email,
            name=name,
            role=role,
            email_verified=True,
        )
        db.add(user)
        await db.flush()
        logger.info('Created demo user email=%s id=%s', normalized_email, user.id)
    else:
        if user.role not in (PLATFORM_ROLE_SUPER_ADMIN,):
            user.role = role
        if name and not user.name:
            user.name = name

    membership = (
        await db.execute(
            select(Membership).where(
                Membership.user_id == user.id,
                Membership.tenant_id == tenant.id,
            )
        )
    ).scalar_one_or_none()
    if not membership:
        membership = Membership(
            user_id=user.id,
            tenant_id=tenant.id,
            role=role,
            status='active',
        )
        db.add(membership)
    else:
        membership.role = role
        membership.status = 'active'

    await db.commit()
    await db.refresh(user)
    await db.refresh(tenant)

    return str(user.id), str(tenant.id), role


async def resolve_db_user_session(
    db: AsyncSession,
    email: str,
) -> Optional[tuple[str, str, str, str]]:
    """Load tenant session for an existing DB user (first active membership).

    Returns:
        (user_id, email, tenant_id, membership_role) or None
    """
    normalized = email.strip().lower()
    user = (
        await db.execute(select(User).where(User.email == normalized))
    ).scalar_one_or_none()
    if not user:
        return None

    result = await db.execute(
        select(Membership)
        .where(
            Membership.user_id == user.id,
            Membership.status == 'active',
        )
        .order_by(Membership.joined_at.desc())
        .limit(1)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        return None

    return (
        str(user.id),
        user.email,
        str(membership.tenant_id),
        membership.role,
    )
