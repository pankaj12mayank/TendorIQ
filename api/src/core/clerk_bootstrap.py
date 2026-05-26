"""Link Clerk users to TenderIQ DB users and tenant memberships."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .logging import get_logger
from .models import Membership, User, generate_uuid
from .roles import coerce_membership_role, normalize_membership_role

logger = get_logger('clerk_bootstrap')


def _clerk_email(clerk_user: dict[str, Any]) -> Optional[str]:
    addresses = clerk_user.get('email_addresses') or []
    if not addresses:
        return None
    first = addresses[0] if isinstance(addresses, list) else addresses
    if isinstance(first, dict):
        return (first.get('email_address') or '').strip().lower() or None
    return None


def _clerk_name(clerk_user: dict[str, Any], email: Optional[str]) -> str:
    first = (clerk_user.get('first_name') or '').strip()
    last = (clerk_user.get('last_name') or '').strip()
    full = f'{first} {last}'.strip()
    if full:
        return full
    if email and '@' in email:
        return email.split('@')[0]
    return 'User'


async def ensure_clerk_user(
    db: AsyncSession,
    clerk_user: dict[str, Any],
) -> User:
    """Upsert application user row for a Clerk identity."""
    clerk_id = str(clerk_user.get('id') or '')
    if not clerk_id:
        raise ValueError('Clerk user id missing')

    email = _clerk_email(clerk_user)
    if not email:
        raise ValueError('Clerk user email missing')

    metadata = clerk_user.get('public_metadata') or {}
    role_hint = coerce_membership_role(
        metadata.get('membership_role') or metadata.get('role'),
        default='member',
    )
    name = _clerk_name(clerk_user, email)

    user = (
        await db.execute(select(User).where(User.clerk_id == clerk_id))
    ).scalar_one_or_none()
    if not user:
        by_email = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if by_email:
            user = by_email
            user.clerk_id = clerk_id
        else:
            user = User(
                id=generate_uuid(),
                email=email,
                name=name,
                role=role_hint,
                clerk_id=clerk_id,
                email_verified=True,
            )
            db.add(user)
            await db.flush()
            logger.info('Created user for Clerk id=%s email=%s', clerk_id, email)
    else:
        if name and not user.name:
            user.name = name
        if user.role not in ('owner', 'admin', 'manager', 'analyst', 'member', 'viewer'):
            user.role = role_hint

    await db.commit()
    await db.refresh(user)
    return user


async def resolve_clerk_auth_context(
    db: AsyncSession,
    clerk_user: dict[str, Any],
) -> Optional[tuple[str, str, Optional[str], str, Optional[str]]]:
    """Lookup DB user for Clerk identity. Returns (user_id, email, tenant_id, membership_role, name)."""
    clerk_id = str(clerk_user.get('id') or '')
    if not clerk_id:
        return None

    user = (
        await db.execute(select(User).where(User.clerk_id == clerk_id))
    ).scalar_one_or_none()
    if not user:
        email = _clerk_email(clerk_user)
        if email:
            user = (
                await db.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
    if not user:
        return None

    user_id, tenant_id, membership_role = await resolve_clerk_tenant_session(db, user)
    return (user_id, user.email, tenant_id, membership_role, user.name)


async def resolve_clerk_tenant_session(
    db: AsyncSession,
    user: User,
) -> tuple[str, Optional[str], str]:
    """Return (user_id, tenant_id, membership_role) for JWT issuance."""
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
    role = normalize_membership_role(user.role) or 'member'
    return (str(user.id), None, role)
