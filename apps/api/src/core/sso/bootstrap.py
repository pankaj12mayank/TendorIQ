"""Provision users and memberships after IdP authentication."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..local_auth import issue_session_tokens, login_user_payload
from ..models import Membership, User, generate_uuid
from ..roles import coerce_membership_role, normalize_membership_role
from . import SSOUser


async def ensure_sso_membership(
    db: AsyncSession,
    *,
    user: User,
    tenant_id: UUID,
    membership_role: str,
) -> str:
    role = coerce_membership_role(membership_role, default='member')
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.tenant_id == tenant_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership:
        membership.role = role
        membership.status = 'active'
    else:
        db.add(
            Membership(
                user_id=user.id,
                tenant_id=tenant_id,
                role=role,
                status='active',
            )
        )
    await db.commit()
    return role


async def ensure_sso_user(
    db: AsyncSession,
    sso_user: SSOUser,
    *,
    membership_role: str = 'member',
) -> User:
    email = sso_user.email.strip().lower()
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user:
        name = ' '.join(filter(None, [sso_user.first_name, sso_user.last_name])).strip() or email.split('@')[0]
        user = User(
            id=generate_uuid(),
            email=email,
            name=name,
            role=coerce_membership_role(membership_role),
            email_verified=True,
        )
        db.add(user)
        await db.flush()
    await db.commit()
    await db.refresh(user)
    return user


async def exchange_sso_session(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    sso_user: SSOUser,
    membership_role: str,
) -> dict:
    user = await ensure_sso_user(db, sso_user, membership_role=membership_role)
    role = await ensure_sso_membership(
        db,
        user=user,
        tenant_id=tenant_id,
        membership_role=membership_role,
    )
    tokens = issue_session_tokens(
        user_id=str(user.id),
        email=user.email,
        role=role,
        tenant_id=str(tenant_id),
        membership_role=role,
    )
    return {
        'tokens': tokens,
        'user': login_user_payload(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            role=role,
            membership_role=role,
            tenant_id=str(tenant_id),
            is_super_admin=False,
        ),
    }
