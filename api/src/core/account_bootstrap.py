"""Resolve tenant session for database-backed users."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Membership, User


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
