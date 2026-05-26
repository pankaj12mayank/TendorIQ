"""Personal workspace bootstrap — one implicit tenant per user (legacy storage)."""

from __future__ import annotations

import re
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .logging import get_logger
from .models import CompanyProfile, Membership, Tenant, User, generate_uuid, pk_str

logger = get_logger('personal_workspace')


def _slug_for_user(user_id: str) -> str:
    safe = re.sub(r'[^a-z0-9]+', '-', user_id.lower())[:40].strip('-')
    return f'user-{safe or "workspace"}'


async def ensure_personal_workspace(
    db: AsyncSession,
    user_id: str,
    email: Optional[str] = None,
    *,
    display_name: Optional[str] = None,
) -> tuple[str, str]:
    """Ensure user has an active membership + company profile.

    Returns:
        (tenant_id, membership_role)
    """
    uid = pk_str(user_id)
    user = await db.get(User, uid)
    if not user:
        raise ValueError(f'User not found: {user_id}')

    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == uid, Membership.status == 'active')
        .order_by(Membership.joined_at.desc())
        .limit(1)
    )
    membership = result.scalar_one_or_none()
    if membership:
        await _ensure_company_profile(db, uid, display_name or user.name, email or user.email)
        return str(membership.tenant_id), membership.role

    slug_base = _slug_for_user(str(user.id))
    slug = slug_base
    suffix = 0
    while True:
        existing = (
            await db.execute(select(Tenant).where(Tenant.slug == slug))
        ).scalar_one_or_none()
        if not existing:
            break
        suffix += 1
        slug = f'{slug_base}-{suffix}'

    tenant = Tenant(
        id=generate_uuid(),
        name=display_name or user.name or (email or 'My Workspace').split('@')[0],
        slug=slug,
        plan='free',
        status='active',
    )
    db.add(tenant)
    await db.flush()

    membership = Membership(
        user_id=uid,
        tenant_id=tenant.id,
        role='owner',
        status='active',
    )
    db.add(membership)
    await _ensure_company_profile(db, uid, tenant.name, email or user.email)
    await db.commit()
    logger.info('Created personal workspace tenant=%s user=%s', tenant.id, user.id)
    return str(tenant.id), membership.role


async def _ensure_company_profile(
    db: AsyncSession,
    user_id: str,
    company_name: Optional[str],
    email: Optional[str],
) -> CompanyProfile:
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        if company_name and not profile.company_name:
            profile.company_name = company_name
        return profile

    profile = CompanyProfile(
        user_id=user_id,
        company_name=company_name or (email.split('@')[0] if email else 'My Company'),
    )
    db.add(profile)
    await db.flush()
    return profile


async def get_company_profile_dict(db: AsyncSession, user_id: str) -> Optional[dict]:
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == pk_str(user_id))
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    meta = row.metadata_json if isinstance(row.metadata_json, dict) else {}
    return {
        'id': str(row.id),
        'user_id': str(row.user_id),
        'company_name': row.company_name,
        'industry': row.industry,
        'address': row.address,
        'phone': row.phone,
        'website': row.website,
        'tax_id': row.tax_id,
        'logo_url': row.logo_url,
        'ai_preferences': meta.get('ai_preferences') or {},
    }


async def get_ai_preferences_dict(db: AsyncSession, user_id: str) -> dict:
    profile = await get_company_profile_dict(db, user_id)
    if not profile:
        return {}
    prefs = profile.get('ai_preferences')
    return prefs if isinstance(prefs, dict) else {}


async def update_ai_preferences_dict(
    db: AsyncSession,
    user_id: str,
    updates: dict,
) -> dict:
    from uuid import UUID

    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == pk_str(user_id))
    )
    row = result.scalar_one_or_none()
    if not row:
        return {}
    meta = dict(row.metadata_json or {})
    current = meta.get('ai_preferences') if isinstance(meta.get('ai_preferences'), dict) else {}
    current.update({k: v for k, v in updates.items() if v is not None})
    meta['ai_preferences'] = current
    row.metadata_json = meta
    await db.commit()
    await db.refresh(row)
    return current
