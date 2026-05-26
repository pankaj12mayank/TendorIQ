"""Link Supabase Auth users to TenderIQ DB users and personal workspace."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .logging import get_logger
from .models import Membership, User, generate_uuid
from .personal_workspace import ensure_personal_workspace
from .roles import coerce_membership_role, normalize_membership_role
from .supabase_auth import claims_email, claims_name

logger = get_logger('supabase_bootstrap')


async def ensure_supabase_user(
    db: AsyncSession,
    claims: dict[str, Any],
) -> User:
    """Upsert application user for a Supabase identity."""
    supabase_id = str(claims.get('sub') or '')
    if not supabase_id:
        raise ValueError('Supabase user id missing')

    email = claims_email(claims)
    if not email:
        raise ValueError('Supabase user email missing')

    meta = claims.get('user_metadata') or {}
    role_hint = 'member'
    if isinstance(meta, dict):
        role_hint = coerce_membership_role(
            meta.get('membership_role') or meta.get('role'),
            default='member',
        )
    name = claims_name(claims, email)

    user = (
        await db.execute(select(User).where(User.supabase_id == supabase_id))
    ).scalar_one_or_none()
    if not user:
        by_email = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if by_email:
            user = by_email
            user.supabase_id = supabase_id
        else:
            user = User(
                id=generate_uuid(),
                email=email,
                name=name,
                role=role_hint,
                supabase_id=supabase_id,
                email_verified=bool(claims.get('email_confirmed_at')),
            )
            db.add(user)
            await db.flush()
            logger.info('Created user for Supabase id=%s email=%s', supabase_id, email)
    else:
        if name and not user.name:
            user.name = name
        if not user.email_verified and claims.get('email_confirmed_at'):
            user.email_verified = True

    await db.commit()
    await db.refresh(user)
    return user


async def resolve_supabase_session(
    db: AsyncSession,
    user: User,
) -> tuple[str, Optional[str], str]:
    """Return (user_id, tenant_id, membership_role) for API JWT issuance."""
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
    if membership:
        return (
            str(user.id),
            str(membership.tenant_id),
            normalize_membership_role(membership.role) or 'member',
        )

    tenant_id, membership_role = await ensure_personal_workspace(
        db,
        str(user.id),
        user.email,
        display_name=user.name,
    )
    return str(user.id), tenant_id, membership_role


async def resolve_supabase_auth_context(
    db: AsyncSession,
    claims: dict[str, Any],
) -> Optional[tuple[str, str, Optional[str], str, Optional[str]]]:
    """Returns (user_id, email, tenant_id, membership_role, name)."""
    user = await ensure_supabase_user(db, claims)
    user_id, tenant_id, membership_role = await resolve_supabase_session(db, user)
    return (user_id, user.email, tenant_id, membership_role, user.name)
