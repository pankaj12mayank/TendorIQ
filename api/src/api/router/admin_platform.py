"""Platform admin API — users and usage summary (TenderIQ Lite)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from ...core.database import get_db
from ...core.models import Document, Membership, Tenant, UsageLog, User
from ...core.platform.lite_settings import SETTING_KEYS, get_all_settings, patch_setting
from ...core.roles import MEMBERSHIP_ROLES, coerce_membership_role
from ..dependencies.auth import SuperAdmin

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/admin/platform', tags=['Admin Platform'])


class PlatformUserBody(BaseModel):
    name: str
    email: str
    role: str = 'member'
    status: str = 'active'
    organization: Optional[str] = None


class PlatformUserPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    organization: Optional[str] = None


class PlatformSettingsPatch(BaseModel):
    section: str
    data: dict


def _map_db_user(
    u: User,
    tenant_name: str = '—',
    membership_role: Optional[str] = None,
) -> dict:
    role = membership_role or (u.role if u.role in MEMBERSHIP_ROLES else 'member')
    return {
        'id': str(u.id),
        'name': u.name or u.email.split('@')[0],
        'email': u.email,
        'role': role,
        'membership_role': role,
        'status': 'active',
        'organization': tenant_name,
        'lastActive': (u.last_login_at or u.updated_at or datetime.now(timezone.utc)).isoformat(),
        'createdAt': (u.created_at or datetime.now(timezone.utc)).isoformat(),
    }


@router.get('/users')
async def list_users(
    _admin: SuperAdmin,
    search: Optional[str] = Query(None),
    db=Depends(get_db),
):
    users: list[dict] = []
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(500))
    for u in result.scalars().all():
        mem_result = await db.execute(
            select(Membership)
            .where(Membership.user_id == u.id, Membership.status == 'active')
            .order_by(Membership.joined_at.desc())
            .limit(1)
        )
        mem = mem_result.scalar_one_or_none()
        tenant_name = '—'
        mem_role = None
        if mem:
            t = await db.get(Tenant, mem.tenant_id)
            tenant_name = t.name if t else '—'
            mem_role = mem.role
        row = _map_db_user(u, tenant_name, mem_role)
        if search:
            q = search.lower()
            if q not in row['email'].lower() and q not in row['name'].lower():
                continue
        users.append(row)
    return {'success': True, 'data': users}


@router.get('/analytics/summary')
async def usage_summary(_admin: SuperAdmin, db=Depends(get_db)):
    """Lightweight platform usage totals for admin dashboard."""
    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_actions = await db.scalar(select(func.count(UsageLog.id))) or 0
    ai_tokens = await db.scalar(
        select(func.coalesce(func.sum(UsageLog.tokens_used), 0))
    ) or 0
    return {
        'success': True,
        'data': {
            'total_users': total_users,
            'total_actions': total_actions,
            'ai_tokens_used': int(ai_tokens),
            'generated_at': datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get('/health')
async def platform_health(_admin: SuperAdmin):
    return {
        'success': True,
        'data': {
            'status': 'healthy',
            'checked_at': datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get('/settings')
async def get_platform_settings(_admin: SuperAdmin, db=Depends(get_db)):
    if not db:
        raise HTTPException(status_code=500, detail='Database unavailable')
    data = await get_all_settings(db)
    return {'success': True, 'data': data, 'sections': list(SETTING_KEYS)}


@router.patch('/settings')
async def patch_platform_settings(
    body: PlatformSettingsPatch,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    section = (body.section or '').strip().lower()
    if section not in SETTING_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid section. Use one of: {", ".join(SETTING_KEYS)}',
        )
    if not isinstance(body.data, dict):
        raise HTTPException(status_code=400, detail='data must be an object')
    try:
        merged = await patch_setting(db, section, body.data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'success': True, 'data': {section: merged}}


@router.get('/uploads')
async def list_platform_uploads(
    _admin: SuperAdmin,
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    """Recent documents across all workspaces."""
    result = await db.execute(
        select(Document)
        .where(Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
        .limit(limit)
    )
    rows: list[dict] = []
    for doc in result.scalars().all():
        owner_email = '—'
        if doc.owner_id:
            u = await db.get(User, doc.owner_id)
            if u:
                owner_email = u.email
        tenant_name = '—'
        if doc.tenant_id:
            t = await db.get(Tenant, doc.tenant_id)
            if t:
                tenant_name = t.name
        rows.append(
            {
                'id': str(doc.id),
                'name': doc.name or doc.file_name,
                'file_name': doc.file_name,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'status': doc.processing_status,
                'owner_email': owner_email,
                'tenant_name': tenant_name,
                'created_at': (doc.created_at or datetime.now(timezone.utc)).isoformat(),
            }
        )
    return {'success': True, 'data': rows}
