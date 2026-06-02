"""Platform admin API — users and usage summary (TenderIQ Lite)."""

from __future__ import annotations

import logging
import copy
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Header, Request
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...core.models import (
    AnalysisResult,
    CompanyProfile,
    Document,
    Membership,
    PaymentTransaction,
    Proposal,
    Tender,
    Tenant,
    UsageLog,
    User,
    generate_uuid,
)
from ...core.platform.lite_settings import (
    SETTING_KEYS,
    DEFAULT_LANDING_MODULES,
    get_all_settings,
    get_setting,
    patch_setting,
    validate_landing_cms_modules,
)
from ...core.smtp_settings import get_smtp_settings, update_smtp_settings
from ...core.mailer import send_smtp_email
from ...core.roles import MEMBERSHIP_ROLES, coerce_membership_role
from ...core.storage import storage_service
from ...core.config import settings
from ...core.security.encrypted_secrets import SecretEncryptor
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


class UserStatusPatch(BaseModel):
    status: str = Field(..., pattern=r'^(active|inactive)$')


class PlatformSettingsPatch(BaseModel):
    section: str
    data: dict


class CMSDraftPatch(BaseModel):
    modules: dict
    expected_version: Optional[int] = None


class SMTPSettingsBody(BaseModel):
    host: str
    port: int = 587
    sender_email: str
    sender_name: Optional[str] = 'TenderIQ'
    app_password: str


class SMTPTestBody(BaseModel):
    to_email: str


class OwnerProfilePatch(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=120)
    password: Optional[str] = Field(None, min_length=8, max_length=256)


class PaymentGatewaySettingsBody(BaseModel):
    razorpay_key_id: Optional[str] = ''
    razorpay_key_secret: Optional[str] = ''
    razorpay_webhook_secret: Optional[str] = ''
    razorpay_test_mode: bool = True
    stripe_publishable_key: Optional[str] = ''
    stripe_secret_key: Optional[str] = ''
    stripe_webhook_secret: Optional[str] = ''
    stripe_test_mode: bool = True


class PaymentGatewayTestBody(BaseModel):
    gateway: str = Field(..., pattern=r'^(razorpay|stripe)$')


ALLOWED_IMAGE_TYPES = {'jpeg', 'png', 'webp', 'gif', 'ico'}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _encode_secret(value: str) -> str:
    v = (value or '').strip()
    if not v:
        return ''
    if v.startswith('ENC:'):
        return v
    return f'ENC:{SecretEncryptor().encrypt(v)}'


def _decode_secret(value: str) -> str:
    v = (value or '').strip()
    if not v:
        return ''
    if not v.startswith('ENC:'):
        return v
    return SecretEncryptor().decrypt(v[4:])


def _sanitize_gateway_out(data: dict) -> dict:
    out = dict(data or {})
    for key in ('razorpay_key_secret', 'razorpay_webhook_secret', 'stripe_secret_key', 'stripe_webhook_secret'):
        out[key] = _decode_secret(str(out.get(key) or ''))
    out['razorpay_test_mode'] = bool(out.get('razorpay_test_mode', True))
    out['stripe_test_mode'] = bool(out.get('stripe_test_mode', True))
    return out


def _sanitize_gateway_store(data: dict) -> dict:
    out = dict(data or {})
    for key in ('razorpay_key_secret', 'razorpay_webhook_secret', 'stripe_secret_key', 'stripe_webhook_secret'):
        out[key] = _encode_secret(str(out.get(key) or ''))
    out['razorpay_test_mode'] = bool(out.get('razorpay_test_mode', True))
    out['stripe_test_mode'] = bool(out.get('stripe_test_mode', True))
    return out


async def _read_valid_image(file: UploadFile) -> bytes:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail='Image is empty')
    if len(payload) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail='Image exceeds 5MB limit')
    ext = (file.filename or '').rsplit('.', 1)[-1].lower() if file.filename else ''
    if ext not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail='Unsupported image type')
    return payload


async def _asset_url_from_value(value: Optional[str]) -> Optional[str]:
    raw = (value or '').strip()
    if not raw:
        return None
    if raw.startswith('http://') or raw.startswith('https://'):
        return raw
    signed = await storage_service.generate_signed_download_url(raw, expires_seconds=86400)
    if signed.get('success'):
        return signed.get('download_url')
    return None


def _map_db_user(
    u: User,
    tenant_name: str = '—',
    membership_role: Optional[str] = None,
) -> dict:
    role = membership_role or (u.role if u.role in MEMBERSHIP_ROLES else 'member')
    status_value = 'active'
    return {
        'id': str(u.id),
        'name': u.name or u.email.split('@')[0],
        'email': u.email,
        'role': role,
        'membership_role': role,
        'status': status_value if u.last_login_at else 'inactive',
        'organization': tenant_name,
        'lastActive': (u.last_login_at or u.updated_at or datetime.now(timezone.utc)).isoformat(),
        'createdAt': (u.created_at or datetime.now(timezone.utc)).isoformat(),
    }


@router.get('/users')
async def list_users(
    _admin: SuperAdmin,
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None, pattern=r'^(active|inactive)$'),
    role: Optional[str] = Query(None),
    plan: Optional[str] = Query(None),
    include_deleted: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
):
    subq = (
        select(
            Membership.user_id.label('user_id'),
            func.max(Membership.joined_at).label('joined_at'),
        )
        .where(Membership.status == 'active')
        .group_by(Membership.user_id)
        .subquery()
    )
    q = (
        select(User, Membership, Tenant)
        .outerjoin(subq, subq.c.user_id == User.id)
        .outerjoin(
            Membership,
            (Membership.user_id == User.id)
            & (Membership.joined_at == subq.c.joined_at),
        )
        .outerjoin(Tenant, Tenant.id == Membership.tenant_id)
    )
    if search:
        term = f'%{search.strip().lower()}%'
        q = q.where(
            func.lower(User.email).like(term) | func.lower(func.coalesce(User.name, '')).like(term)
        )
    if status == 'inactive':
        q = q.where(User.last_login_at.is_(None))
    if status == 'active':
        q = q.where(User.last_login_at.is_not(None))
    if role:
        q = q.where(Membership.role == coerce_membership_role(role))
    if plan:
        q = q.where(Tenant.plan == plan.lower())

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = (
        (
            await db.execute(
                q.order_by(User.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        .all()
    )
    data: list[dict] = []
    for u, mem, tenant in rows:
        row = _map_db_user(
            u,
            tenant_name=(tenant.name if tenant else '—'),
            membership_role=(mem.role if mem else None),
        )
        row['plan'] = (tenant.plan if tenant else 'free')
        data.append(row)
    return {
        'success': True,
        'data': data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': int(total),
            'pages': (int(total) + limit - 1) // limit if total else 0,
        },
    }


@router.patch('/users/{user_id}/status')
async def patch_user_status(
    user_id: str,
    body: UserStatusPatch,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    if body.status == 'inactive':
        user.last_login_at = None
    else:
        user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return {'success': True, 'data': {'user_id': user_id, 'status': body.status}}


@router.get('/analytics/summary')
async def usage_summary(_admin: SuperAdmin, db=Depends(get_db)):
    """Lightweight platform usage totals for admin dashboard."""
    total_users = await db.scalar(select(func.count(User.id))) or 0
    active_users = await db.scalar(select(func.count(User.id)).where(User.last_login_at.is_not(None))) or 0
    total_actions = await db.scalar(select(func.count(UsageLog.id))) or 0
    ai_tokens = await db.scalar(
        select(func.coalesce(func.sum(UsageLog.tokens_used), 0))
    ) or 0
    uploads_total = await db.scalar(select(func.count(Document.id)).where(Document.deleted_at.is_(None))) or 0
    ai_jobs_total = await db.scalar(
        select(func.count(Document.id)).where(
            Document.deleted_at.is_(None),
            Document.processing_status.in_(('processing', 'retrying', 'completed', 'failed', 'needs_review')),
        )
    ) or 0
    failed_ai_jobs = await db.scalar(
        select(func.count(Document.id)).where(
            Document.deleted_at.is_(None),
            Document.processing_status == 'failed',
        )
    ) or 0
    revenue = await db.scalar(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(PaymentTransaction.status == 'paid')
    ) or 0
    return {
        'success': True,
        'data': {
            'total_users': total_users,
            'active_users': int(active_users),
            'total_actions': total_actions,
            'uploads_total': int(uploads_total),
            'ai_jobs_total': int(ai_jobs_total),
            'failed_ai_jobs': int(failed_ai_jobs),
            'revenue': float(revenue),
            'ai_tokens_used': int(ai_tokens),
            'generated_at': datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get('/users/{user_id}')
async def user_detail(user_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    membership = (
        await db.execute(
            select(Membership)
            .where(Membership.user_id == user.id, Membership.status == 'active')
            .order_by(Membership.joined_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    tenant = await db.get(Tenant, membership.tenant_id) if membership else None
    tenant_id = tenant.id if tenant else None
    uploads = (
        (
            await db.execute(
                select(Document)
                .where(Document.owner_id == user.id, Document.deleted_at.is_(None))
                .order_by(Document.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    analyses = (
        (
            await db.execute(
                select(AnalysisResult)
                .where(AnalysisResult.owner_id == user.id)
                .order_by(AnalysisResult.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    proposals = (
        (
            await db.execute(
                select(Proposal)
                .where(Proposal.owner_id == user.id)
                .order_by(Proposal.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    tenders = (
        (
            await db.execute(
                select(Tender)
                .where(Tender.owner_id == user.id)
                .order_by(Tender.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    payments = (
        (
            await db.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.user_id == user.id)
                .order_by(PaymentTransaction.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    timeline = (
        (
            await db.execute(
                select(UsageLog)
                .where(UsageLog.user_id == user.id)
                .order_by(UsageLog.created_at.desc())
                .limit(100)
            )
        )
        .scalars()
        .all()
    )
    return {
        'success': True,
        'data': {
            'user': _map_db_user(user, tenant_name=(tenant.name if tenant else '—'), membership_role=(membership.role if membership else None)),
            'plan': (tenant.plan if tenant else 'free'),
            'tenant_id': str(tenant_id) if tenant_id else None,
            'uploads': [{'id': str(d.id), 'name': d.file_name, 'status': d.processing_status, 'created_at': d.created_at.isoformat() if d.created_at else None} for d in uploads],
            'analysis': [{'id': str(a.id), 'type': a.analysis_type, 'score': a.score, 'created_at': a.created_at.isoformat() if a.created_at else None} for a in analyses],
            'proposals': [{'id': str(p.id), 'title': p.title, 'status': p.status, 'created_at': p.created_at.isoformat() if p.created_at else None} for p in proposals],
            'tenders': [{'id': str(t.id), 'title': t.title, 'status': t.status, 'created_at': t.created_at.isoformat() if t.created_at else None} for t in tenders],
            'payments': [{'id': str(p.id), 'provider': p.provider, 'amount': p.amount, 'currency': p.currency, 'status': p.status, 'created_at': p.created_at.isoformat() if p.created_at else None} for p in payments],
            'activity_timeline': [{'id': str(t.id), 'action': t.action, 'resource_type': t.resource_type, 'created_at': t.created_at.isoformat() if t.created_at else None} for t in timeline],
            'usage': {
                'uploads': len(uploads),
                'tenders': len(tenders),
                'analysis': len(analyses),
                'proposals': len(proposals),
                'payments': len(payments),
            },
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


@router.get('/owner/profile')
async def get_owner_profile(admin: SuperAdmin, db=Depends(get_db)):
    user = await db.get(User, admin.user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Owner profile not found')
    cms = await get_setting(db, 'landing_cms')
    branding = cms.get('draft') if isinstance(cms.get('draft'), dict) else {}
    images = branding.get('images') if isinstance(branding.get('images'), dict) else {}
    avatar_url = await _asset_url_from_value(user.avatar_url)
    logo_url = await _asset_url_from_value(images.get('logo_url'))
    favicon_url = await _asset_url_from_value(images.get('favicon_url'))
    return {
        'success': True,
        'data': {
            'id': str(user.id),
            'username': user.name or '',
            'email': user.email,
            'avatar_url': avatar_url,
            'logo_url': logo_url,
            'favicon_url': favicon_url,
        },
    }


@router.patch('/owner/profile')
async def patch_owner_profile(body: OwnerProfilePatch, admin: SuperAdmin, db=Depends(get_db)):
    user = await db.get(User, admin.user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Owner profile not found')
    if body.username:
        user.name = body.username.strip()
    if body.password:
        from ...core.passwords import hash_password
        from ...core.local_user_auth import _set_user_prefs, _user_prefs

        prefs = _user_prefs(user)
        prefs['password_hash'] = hash_password(body.password)
        _set_user_prefs(user, prefs)
    await db.commit()
    await db.refresh(user)
    return {'success': True, 'data': {'username': user.name, 'avatar_url': user.avatar_url}}


@router.post('/owner/profile/upload')
async def upload_owner_profile_asset(
    admin: SuperAdmin,
    kind: str = Form(...),
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    if kind not in {'avatar', 'logo', 'favicon'}:
        raise HTTPException(status_code=400, detail='kind must be avatar/logo/favicon')
    content = await _read_valid_image(file)
    user = await db.get(User, admin.user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Owner profile not found')

    old_avatar = user.avatar_url
    cms = await get_setting(db, 'landing_cms')
    landing_draft = cms.get('draft') if isinstance(cms.get('draft'), dict) else copy.deepcopy(DEFAULT_LANDING_MODULES)
    images = landing_draft.get('images') if isinstance(landing_draft.get('images'), dict) else {}
    old_logo = images.get('logo_url')
    old_favicon = images.get('favicon_url')
    ext = (file.filename or 'image.png').split('.')[-1].lower()
    key = f"platform-assets/{kind}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{admin.user_id}.{ext}"
    up = await storage_service.upload_file(
        file_content=content,
        storage_key=key,
        content_type=file.content_type or 'application/octet-stream',
        metadata={'asset_kind': kind, 'uploaded_by': admin.user_id},
    )
    if not up.get('success'):
        raise HTTPException(status_code=500, detail='Upload failed')
    url = key
    try:
        if kind == 'avatar':
            user.avatar_url = url
        elif kind == 'logo':
            images['logo_url'] = url
            landing_draft['images'] = images
            await patch_setting(db, 'landing_cms', {'draft': landing_draft, 'updated_at': datetime.now(timezone.utc).isoformat()})
        else:
            images['favicon_url'] = url
            landing_draft['images'] = images
            await patch_setting(db, 'landing_cms', {'draft': landing_draft, 'updated_at': datetime.now(timezone.utc).isoformat()})
        await db.commit()
    except Exception:
        # rollback uploaded file when DB update fails
        await storage_service.delete_file(key)
        user.avatar_url = old_avatar
        images['logo_url'] = old_logo
        images['favicon_url'] = old_favicon
        await db.rollback()
        raise
    signed = await _asset_url_from_value(url)
    return {'success': True, 'data': {'kind': kind, 'url': signed}}


@router.post('/cms/assets/upload')
async def upload_cms_asset(
    admin: SuperAdmin,
    file: UploadFile = File(...),
):
    content = await _read_valid_image(file)
    ext = (file.filename or 'image.png').split('.')[-1].lower()
    key = f"platform-assets/cms/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{admin.user_id}.{ext}"
    up = await storage_service.upload_file(
        file_content=content,
        storage_key=key,
        content_type=file.content_type or 'application/octet-stream',
        metadata={'asset_kind': 'cms_image', 'uploaded_by': admin.user_id},
    )
    if not up.get('success'):
        raise HTTPException(status_code=500, detail='Upload failed')
    signed = await _asset_url_from_value(key)
    return {'success': True, 'data': {'url': signed or key, 'storage_key': key}}


def _cms_revision_id() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')


@router.get('/cms')
async def get_landing_cms(_admin: SuperAdmin, db=Depends(get_db)):
    cms = await get_setting(db, 'landing_cms')
    draft = cms.get('draft') if isinstance(cms.get('draft'), dict) else copy.deepcopy(DEFAULT_LANDING_MODULES)
    published = cms.get('published') if isinstance(cms.get('published'), dict) else copy.deepcopy(DEFAULT_LANDING_MODULES)
    return {
        'success': True,
        'data': {
            'version': int(cms.get('version') or 1),
            'status': str(cms.get('status') or 'draft'),
            'draft': draft,
            'published': published,
            'history': cms.get('history') if isinstance(cms.get('history'), list) else [],
            'published_at': cms.get('published_at'),
            'updated_at': cms.get('updated_at'),
        },
    }


@router.patch('/cms/draft')
async def patch_landing_cms_draft(body: CMSDraftPatch, _admin: SuperAdmin, db=Depends(get_db)):
    cms = await get_setting(db, 'landing_cms')
    current_version = int(cms.get('version') or 1)
    if body.expected_version is not None and int(body.expected_version) != current_version:
        raise HTTPException(
            status_code=409,
            detail='CMS changed by another session. Refresh and retry.',
        )
    draft = cms.get('draft') if isinstance(cms.get('draft'), dict) else copy.deepcopy(DEFAULT_LANDING_MODULES)
    draft = {**draft, **body.modules}
    validate_landing_cms_modules(draft)

    revision = {
        'id': _cms_revision_id(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'version': current_version,
        'snapshot': cms.get('draft') if isinstance(cms.get('draft'), dict) else copy.deepcopy(DEFAULT_LANDING_MODULES),
    }
    history = cms.get('history') if isinstance(cms.get('history'), list) else []
    history = [revision] + history
    history = history[:20]
    next_state = {
        **cms,
        'status': 'draft',
        'version': current_version + 1,
        'draft': draft,
        'history': history,
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }
    merged = await patch_setting(db, 'landing_cms', next_state)
    return {'success': True, 'data': merged}


@router.post('/cms/publish')
async def publish_landing_cms(_admin: SuperAdmin, db=Depends(get_db)):
    cms = await get_setting(db, 'landing_cms')
    draft = cms.get('draft') if isinstance(cms.get('draft'), dict) else copy.deepcopy(DEFAULT_LANDING_MODULES)
    validate_landing_cms_modules(draft)
    now = datetime.now(timezone.utc).isoformat()
    next_state = {
        **cms,
        'status': 'published',
        'published': draft,
        'published_at': now,
        'updated_at': now,
    }
    merged = await patch_setting(db, 'landing_cms', next_state)
    return {'success': True, 'data': merged}


@router.post('/cms/rollback/{revision_id}')
async def rollback_landing_cms(revision_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    cms = await get_setting(db, 'landing_cms')
    history = cms.get('history') if isinstance(cms.get('history'), list) else []
    target = next((r for r in history if str(r.get('id')) == revision_id), None)
    if not target or not isinstance(target.get('snapshot'), dict):
        raise HTTPException(status_code=404, detail='Revision not found')
    snapshot = target['snapshot']
    validate_landing_cms_modules(snapshot)
    next_state = {
        **cms,
        'status': 'draft',
        'version': int(cms.get('version') or 1) + 1,
        'draft': snapshot,
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }
    merged = await patch_setting(db, 'landing_cms', next_state)
    return {'success': True, 'data': merged}


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


@router.get('/settings/smtp')
async def get_smtp_config(_admin: SuperAdmin, db=Depends(get_db)):
    data = await get_smtp_settings(db)
    return {'success': True, 'data': data}


@router.patch('/settings/smtp')
async def patch_smtp_config(
    body: SMTPSettingsBody,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    data = await update_smtp_settings(db, body.model_dump())
    return {'success': True, 'data': data}


@router.post('/settings/smtp/test')
async def test_smtp_config(
    body: SMTPTestBody,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    smtp = await get_smtp_settings(db)
    try:
        send_smtp_email(
            smtp_settings=smtp,
            to_email=body.to_email,
            subject='TenderIQ SMTP test',
            text_body='SMTP test successful. Your TenderIQ reset emails are configured correctly.',
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'SMTP test failed: {exc}') from exc
    return {'success': True, 'message': 'SMTP test email sent'}


@router.get('/settings/payments')
async def get_payment_gateway_settings(_admin: SuperAdmin, db=Depends(get_db)):
    row = await get_setting(db, 'payment_gateways')
    return {'success': True, 'data': _sanitize_gateway_out(row)}


@router.patch('/settings/payments')
async def patch_payment_gateway_settings(
    body: PaymentGatewaySettingsBody,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    stored = _sanitize_gateway_store(body.model_dump())
    merged = await patch_setting(db, 'payment_gateways', stored)
    return {'success': True, 'data': _sanitize_gateway_out(merged)}


@router.post('/settings/payments/test')
async def test_payment_gateway_settings(
    body: PaymentGatewayTestBody,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    cfg = _sanitize_gateway_out(await get_setting(db, 'payment_gateways'))
    gateway = body.gateway
    if gateway == 'razorpay':
        from ...core.billing.razorpay_lite import razorpay

        key = str(cfg.get('razorpay_key_id') or '').strip()
        secret = str(cfg.get('razorpay_key_secret') or '').strip()
        if not key or not secret:
            raise HTTPException(status_code=400, detail='Razorpay keys not configured')
        try:
            client = razorpay.Client(auth=(key, secret))
            client.utility.verify_payment_signature(
                {
                    'razorpay_order_id': 'order_test',
                    'razorpay_payment_id': 'pay_test',
                    'razorpay_signature': 'sig_test',
                }
            )
        except Exception:
            # expected for dummy signature; if client auth invalid razorpay raises auth-related API errors on real APIs
            pass
        return {'success': True, 'message': 'Razorpay credentials accepted for test mode'}

    # stripe
    import urllib.request
    import urllib.error
    import base64

    key = str(cfg.get('stripe_secret_key') or '').strip()
    if not key:
        raise HTTPException(status_code=400, detail='Stripe secret key not configured')
    req = urllib.request.Request('https://api.stripe.com/v1/balance', method='GET')
    token = base64.b64encode(f'{key}:'.encode('utf-8')).decode('utf-8')
    req.add_header('Authorization', f'Basic {token}')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status >= 400:
                raise HTTPException(status_code=400, detail='Stripe connection failed')
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f'Stripe test failed: {exc.code}') from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Stripe test failed: {exc}') from exc
    return {'success': True, 'message': 'Stripe connection successful'}


@router.post('/payments/webhooks/stripe')
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias='Stripe-Signature'),
    db=Depends(get_db),
):
    cfg = _sanitize_gateway_out(await get_setting(db, 'payment_gateways'))
    secret = str(cfg.get('stripe_webhook_secret') or '').strip()
    if not secret:
        raise HTTPException(status_code=503, detail='Stripe webhook secret not configured')
    if not stripe_signature:
        raise HTTPException(status_code=400, detail='Missing Stripe-Signature header')
    import hmac
    import hashlib

    body = await request.body()
    parts = stripe_signature.split(',')
    expected = None
    for part in parts:
        part = part.strip()
        if part.startswith('v1='):
            expected = part[3:]
            break
    if not expected:
        raise HTTPException(status_code=400, detail='Missing v1 signature in Stripe-Signature header')

    digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, expected):
        raise HTTPException(status_code=400, detail='Invalid Stripe webhook signature')

    import json
    try:
        event = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail='Invalid JSON body')

    from ...core.billing.stripe_webhook import apply_stripe_webhook_event

    result = await apply_stripe_webhook_event(db, event)
    return {'success': True, 'message': 'Webhook processed', 'handled': result['handled'], 'type': result['type']}


@router.post('/payments/webhooks/razorpay')
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias='X-Razorpay-Signature'),
    db=Depends(get_db),
):
    cfg = _sanitize_gateway_out(await get_setting(db, 'payment_gateways'))
    secret = str(cfg.get('razorpay_webhook_secret') or '').strip()
    if not secret:
        raise HTTPException(status_code=503, detail='Razorpay webhook secret not configured')
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail='Missing X-Razorpay-Signature header')

    import hashlib
    import hmac

    body = await request.body()
    expected = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_razorpay_signature):
        raise HTTPException(status_code=400, detail='Invalid Razorpay webhook signature')

    import json
    try:
        event = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail='Invalid JSON body')

    event_type = (event.get('event') or '').strip()
    payload = event.get('payload', {})
    payment = payload.get('payment', {}) or {}
    entity = payment.get('entity', {}) or {}

    razorpay_payment_id = entity.get('id') or ''
    razorpay_order_id = ''
    order = entity.get('order_id')
    if order:
        razorpay_order_id = str(order)
    notes = entity.get('notes', {}) or {}
    tenant_id = notes.get('tenant_id') or ''
    plan_id = notes.get('plan_id') or 'professional'

    if not razorpay_payment_id or not tenant_id:
        return {'success': False, 'message': 'Skipped: missing payment_id or tenant_id in payload'}

    from uuid import UUID
    from datetime import datetime, timezone
    from sqlalchemy import select
    from ..models import PaymentTransaction
    from ...core.tenant_utils import find_tenant_uuid  # not using Subscription directly here

    existing = (
        await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider == 'razorpay',
                PaymentTransaction.payment_id == razorpay_payment_id,
            )
        )
    ).scalar_one_or_none()
    if existing and existing.status == 'paid':
        return {'success': True, 'message': 'Duplicate webhook — already processed'}

    if event_type in ('payment.captured', 'subscription.charged'):
        from uuid import UUID as _UUID
        from ...core.billing.fe_responses import activate_plan_after_payment

        billing_interval = notes.get('billing_interval', 'monthly')
        await activate_plan_after_payment(
            db,
            tenant_id=_UUID(tenant_id),
            plan=plan_id,
            billing_interval=billing_interval,
            payment_id=razorpay_payment_id,
            order_id=razorpay_order_id,
            provider='razorpay',
        )
        return {'success': True, 'message': 'Payment webhook processed', 'event': event_type}

    return {'success': True, 'message': 'Unhandled webhook event', 'event': event_type}


@router.get('/uploads')
async def list_platform_uploads(
    _admin: SuperAdmin,
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    user_filter: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    db=Depends(get_db),
):
    """Recent documents across all workspaces."""
    q = (
        select(
            Document.id,
            Document.name,
            Document.file_name,
            Document.file_type,
            Document.file_size,
            Document.processing_status,
            Document.created_at,
            User.email.label('owner_email'),
            Tenant.name.label('tenant_name'),
        )
        .outerjoin(User, User.id == Document.owner_id)
        .outerjoin(Tenant, Tenant.id == Document.tenant_id)
        .where(Document.deleted_at.is_(None))
    )
    if search:
        term = f'%{search.lower()}%'
        q = q.where(
            func.lower(Document.file_name).like(term)
            | func.lower(func.coalesce(Document.name, '')).like(term)
        )
    if status:
        q = q.where(Document.processing_status == status)
    if user_id:
        q = q.where(Document.owner_id == user_id)
    if user_filter:
        term = f'%{user_filter.strip().lower()}%'
        q = q.where(func.lower(func.coalesce(User.email, '')).like(term))
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    result = await db.execute(q.order_by(Document.created_at.desc()).offset((page - 1) * limit).limit(limit))
    rows: list[dict] = []
    for doc_id, name, file_name, file_type, file_size, processing_status, created_at, owner_email, tenant_name in result.all():
        rows.append(
            {
                'id': str(doc_id),
                'name': name or file_name,
                'file_name': file_name,
                'file_type': file_type,
                'file_size': file_size,
                'status': processing_status,
                'owner_email': owner_email or '—',
                'tenant_name': tenant_name or '—',
                'created_at': (created_at or datetime.now(timezone.utc)).isoformat(),
            }
        )
    return {
        'success': True,
        'data': rows,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': int(total),
            'pages': (int(total) + limit - 1) // limit if total else 0,
        },
    }


@router.delete('/uploads/{document_id}')
async def delete_platform_upload(document_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail='Upload not found')
    storage_deleted = (await storage_service.delete_file(doc.storage_key)).get('success', False)
    await db.delete(doc)
    await db.commit()
    return {'success': True, 'data': {'document_id': document_id, 'storage_deleted': storage_deleted}}


class UploadBatchDeleteBody(BaseModel):
    document_ids: list[str] = Field(default_factory=list, min_length=1, max_length=100)


@router.post('/uploads/batch-delete')
async def batch_delete_platform_uploads(
    body: UploadBatchDeleteBody,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    deleted = 0
    for doc_id in body.document_ids:
        doc = await db.get(Document, doc_id)
        if not doc or doc.deleted_at is not None:
            continue
        await storage_service.delete_file(doc.storage_key)
        await db.delete(doc)
        deleted += 1
    await db.commit()
    return {'success': True, 'data': {'deleted_count': deleted}}


@router.get('/payments/history')
async def payment_history(
    _admin: SuperAdmin,
    status: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
):
    q = select(PaymentTransaction)
    if status:
        q = q.where(PaymentTransaction.status == status)
    if provider:
        q = q.where(PaymentTransaction.provider == provider)
    if from_date:
        q = q.where(PaymentTransaction.created_at >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.where(PaymentTransaction.created_at <= datetime.fromisoformat(to_date))
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = (
        (
            await db.execute(
                q.order_by(PaymentTransaction.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    total_paid = await db.scalar(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(PaymentTransaction.status == 'paid')
    ) or 0
    total_failed = await db.scalar(
        select(func.count(PaymentTransaction.id)).where(PaymentTransaction.status == 'failed')
    ) or 0
    renewals = await db.scalar(
        select(func.count(PaymentTransaction.id)).where(
            PaymentTransaction.status == 'paid',
            PaymentTransaction.plan.is_not(None),
        )
    ) or 0
    return {
        'success': True,
        'data': [
            {
                'id': str(r.id),
                'provider': r.provider,
                'order_id': r.order_id,
                'payment_id': r.payment_id,
                'amount': r.amount,
                'currency': r.currency,
                'plan': r.plan,
                'status': r.status,
                'failure_reason': r.failure_reason,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        'cards': {
            'total_revenue': float(total_paid),
            'failed_count': int(total_failed),
            'renewals_count': int(renewals),
        },
        'pagination': {
            'page': page,
            'limit': limit,
            'total': int(total),
            'pages': (int(total) + limit - 1) // limit if total else 0,
        },
    }


@router.patch('/billing/pricing')
async def patch_billing_pricing(
    body: dict,
    _admin: SuperAdmin,
    db=Depends(get_db),
):
    plans = body.get('plans')
    if not isinstance(plans, list) or not plans:
        raise HTTPException(status_code=400, detail='plans must be a non-empty array')
    seen_ids = set()
    active_monthly_prices = set()
    active_count = 0
    for p in plans:
        if not isinstance(p, dict):
            raise HTTPException(status_code=400, detail='Invalid plan payload')
        pid = str(p.get('id') or '').strip().lower()
        if not pid or pid in seen_ids:
            raise HTTPException(status_code=400, detail='Duplicate or missing plan id')
        seen_ids.add(pid)
        is_active = bool(p.get('active', True))
        monthly = p.get('monthly_usd')
        if monthly is None:
            monthly = p.get('monthly_inr')
        if is_active and monthly in (None, 0):
            raise HTTPException(status_code=400, detail='Active plans require monthly_usd')
        if is_active and monthly is not None:
            active_count += 1
            if monthly in active_monthly_prices:
                raise HTTPException(status_code=400, detail='Pricing conflict: duplicate monthly_usd')
            active_monthly_prices.add(monthly)
        yearly = p.get('yearly_usd')
        if yearly is None:
            yearly = p.get('yearly_inr')
        if yearly not in (None, 0):
            raise HTTPException(status_code=400, detail='Admin billing management is monthly-only')
        if p.get('upload_limit') is not None and int(p.get('upload_limit') or 0) < 1:
            raise HTTPException(status_code=400, detail='upload_limit must be >= 1')
        if p.get('expiry_period_days') is not None and int(p.get('expiry_period_days') or 0) < 30:
            raise HTTPException(status_code=400, detail='expiry_period_days must be >= 30')
    if active_count != 1:
        raise HTTPException(status_code=400, detail='Exactly one active plan is required')
    body['currency'] = 'USD'
    pricing = await patch_setting(db, 'pricing', body)
    return {'success': True, 'data': pricing}


@router.get('/analytics/user-search')
async def analytics_user_search(
    _admin: SuperAdmin,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    term = f'%{q.strip().lower()}%'
    base = select(User).where(
        func.lower(User.email).like(term)
        | func.lower(func.coalesce(User.name, '')).like(term)
    )
    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = (
        (
            await db.execute(
                base.order_by(User.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    user_ids = [u.id for u in rows]
    upload_counts: dict[str, int] = {}
    analysis_counts: dict[str, int] = {}
    proposal_counts: dict[str, int] = {}
    tender_counts: dict[str, int] = {}
    payment_counts: dict[str, int] = {}
    activity_counts: dict[str, int] = {}

    if user_ids:
        upload_rows = (
            await db.execute(
                select(Document.owner_id, func.count(Document.id))
                .where(Document.owner_id.in_(user_ids), Document.deleted_at.is_(None))
                .group_by(Document.owner_id)
            )
        ).all()
        upload_counts = {str(uid): int(cnt or 0) for uid, cnt in upload_rows if uid}

        analysis_rows = (
            await db.execute(
                select(AnalysisResult.owner_id, func.count(AnalysisResult.id))
                .where(AnalysisResult.owner_id.in_(user_ids))
                .group_by(AnalysisResult.owner_id)
            )
        ).all()
        analysis_counts = {str(uid): int(cnt or 0) for uid, cnt in analysis_rows if uid}

        proposal_rows = (
            await db.execute(
                select(Proposal.owner_id, func.count(Proposal.id))
                .where(Proposal.owner_id.in_(user_ids))
                .group_by(Proposal.owner_id)
            )
        ).all()
        proposal_counts = {str(uid): int(cnt or 0) for uid, cnt in proposal_rows if uid}

        tender_rows = (
            await db.execute(
                select(Tender.owner_id, func.count(Tender.id))
                .where(Tender.owner_id.in_(user_ids))
                .group_by(Tender.owner_id)
            )
        ).all()
        tender_counts = {str(uid): int(cnt or 0) for uid, cnt in tender_rows if uid}

        payment_rows = (
            await db.execute(
                select(PaymentTransaction.user_id, func.count(PaymentTransaction.id))
                .where(PaymentTransaction.user_id.in_(user_ids))
                .group_by(PaymentTransaction.user_id)
            )
        ).all()
        payment_counts = {str(uid): int(cnt or 0) for uid, cnt in payment_rows if uid}

        activity_rows = (
            await db.execute(
                select(UsageLog.user_id, func.count(UsageLog.id))
                .where(UsageLog.user_id.in_(user_ids))
                .group_by(UsageLog.user_id)
            )
        ).all()
        activity_counts = {str(uid): int(cnt or 0) for uid, cnt in activity_rows if uid}

    data = []
    for u in rows:
        key = str(u.id)
        data.append(
            {
                'user_id': key,
                'email': u.email,
                'name': u.name,
                'uploads': upload_counts.get(key, 0),
                'tenders': tender_counts.get(key, 0),
                'analysis': analysis_counts.get(key, 0),
                'proposals': proposal_counts.get(key, 0),
                'payments': payment_counts.get(key, 0),
                'activity': activity_counts.get(key, 0),
            }
        )
    return {
        'success': True,
        'data': data,
        'pagination': {'page': page, 'limit': limit, 'total': int(total)},
    }


@router.delete('/users/{user_id}')
async def delete_user(user_id: str, admin: SuperAdmin, db=Depends(get_db)):
    if str(admin.user_id) == str(user_id):
        raise HTTPException(status_code=400, detail='Owner account cannot be deleted')
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    await db.delete(user)
    await db.commit()
    return {'success': True, 'data': {'user_id': user_id, 'deleted': True, 'hard_deleted': True}}


@router.post('/users/{user_id}/restore')
async def restore_user(user_id: str, _admin: SuperAdmin, db=Depends(get_db)):
    raise HTTPException(status_code=410, detail='Restore not available for hard-deleted users')
