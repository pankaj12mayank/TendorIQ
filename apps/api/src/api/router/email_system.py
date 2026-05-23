"""Enterprise email system API — templates, events, SMTP, queue, logs, analytics."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.email.crypto import decrypt_secret, encrypt_secret
from ...core.email.db_models import (
    EmailBranding,
    EmailEvent,
    EmailLog,
    EmailQueueItem,
    EmailTemplate,
    FirebaseConfig,
    SmtpConfig,
)
from ...core.email.events.registry import EVENT_REGISTRY, get_event_definition
from ...core.email.renderers.template_renderer import extract_variables, render_template
from ...core.email.providers.factory import get_provider_chain
from ...core.email.providers.base import OutboundEmail
from ...core.email.providers.factory import send_with_fallback
from ...core.email.services.dispatcher import EmailDispatcher
from ...core.email.services.password_reset import PasswordResetService
from ..dependencies.auth import SuperAdmin, get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/email', tags=['Email System'])


# --- Schemas ---

class TemplateCreate(BaseModel):
    slug: str
    name: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    variables: list[str] = Field(default_factory=list)
    variable_defaults: dict[str, Any] = Field(default_factory=dict)
    sender_name: Optional[str] = None
    reply_to: Optional[str] = None
    branding: dict[str, Any] = Field(default_factory=dict)
    status: str = 'inactive'


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    variables: Optional[list[str]] = None
    variable_defaults: Optional[dict[str, Any]] = None
    sender_name: Optional[str] = None
    reply_to: Optional[str] = None
    branding: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class EventUpdate(BaseModel):
    template_id: Optional[UUID] = None
    is_enabled: Optional[bool] = None
    name: Optional[str] = None


class SmtpConfigCreate(BaseModel):
    name: str = 'Primary SMTP'
    provider: str = 'smtp'
    host: Optional[str] = None
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    encryption: str = 'tls'
    from_email: str
    from_name: str = 'TenderIQ'
    is_primary: bool = False
    is_fallback: bool = False


class FirebaseConfigUpdate(BaseModel):
    project_id: Optional[str] = None
    api_key: Optional[str] = None
    auth_domain: Optional[str] = None
    app_id: Optional[str] = None
    reset_url: Optional[str] = None
    verify_url: Optional[str] = None
    dynamic_link_domain: Optional[str] = None
    is_enabled: bool = False
    use_for_auth_emails: bool = False


class TestSendRequest(BaseModel):
    to: EmailStr
    template_id: Optional[UUID] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    variables: dict[str, Any] = Field(default_factory=dict)


class PreviewRequest(BaseModel):
    subject: str
    html_body: str
    variables: dict[str, Any] = Field(default_factory=dict)


class DispatchRequest(BaseModel):
    event_key: str
    recipient: EmailStr
    variables: dict[str, Any] = Field(default_factory=dict)


class BrandingUpdate(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = '#2563eb'
    accent_color: str = '#7c3aed'
    footer_html: Optional[str] = None
    company_name: str = 'TenderIQ'
    support_email: str = 'support@tenderiq.com'
    website_url: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


def _template_out(t: EmailTemplate) -> dict:
    return {
        'id': str(t.id),
        'slug': t.slug,
        'name': t.name,
        'subject': t.subject,
        'html_body': t.html_body,
        'text_body': t.text_body,
        'variables': t.variables or [],
        'variable_defaults': t.variable_defaults or {},
        'status': t.status,
        'version': t.version,
        'sender_name': t.sender_name,
        'reply_to': t.reply_to,
        'branding': t.branding or {},
        'created_at': t.created_at.isoformat() if t.created_at else None,
        'updated_at': t.updated_at.isoformat() if t.updated_at else None,
    }


# --- Templates ---

@router.get('/templates')
async def list_templates(
    _admin: SuperAdmin,
    status: Optional[str] = None,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(EmailTemplate).where(EmailTemplate.deleted_at.is_(None))
    if status:
        q = q.where(EmailTemplate.status == status)
    elif not include_archived:
        q = q.where(EmailTemplate.status != 'archived')
    q = q.order_by(EmailTemplate.updated_at.desc())
    result = await db.execute(q)
    return [_template_out(t) for t in result.scalars().all()]


@router.post('/templates', status_code=201)
async def create_template(_admin: SuperAdmin, body: TemplateCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(EmailTemplate).where(EmailTemplate.slug == body.slug, EmailTemplate.deleted_at.is_(None))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, 'Template slug already exists')
    tpl = EmailTemplate(
        id=uuid4(),
        slug=body.slug,
        name=body.name,
        subject=body.subject,
        html_body=body.html_body,
        text_body=body.text_body,
        variables=body.variables or extract_variables(body.subject + body.html_body),
        variable_defaults=body.variable_defaults,
        status=body.status,
        sender_name=body.sender_name,
        reply_to=body.reply_to,
        branding=body.branding,
    )
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return _template_out(tpl)


@router.get('/templates/{template_id}')
async def get_template(_admin: SuperAdmin, template_id: UUID, db: AsyncSession = Depends(get_db)):
    tpl = await _get_template(db, template_id)
    return _template_out(tpl)


@router.patch('/templates/{template_id}')
async def update_template(
    _admin: SuperAdmin,
    template_id: UUID,
    body: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    tpl = await _get_template(db, template_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tpl, field, value)
    tpl.version += 1
    await db.commit()
    await db.refresh(tpl)
    return _template_out(tpl)


@router.post('/templates/{template_id}/duplicate', status_code=201)
async def duplicate_template(_admin: SuperAdmin, template_id: UUID, db: AsyncSession = Depends(get_db)):
    tpl = await _get_template(db, template_id)
    copy = EmailTemplate(
        id=uuid4(),
        slug=f'{tpl.slug}-copy-{uuid4().hex[:6]}',
        name=f'{tpl.name} (Copy)',
        subject=tpl.subject,
        html_body=tpl.html_body,
        text_body=tpl.text_body,
        variables=tpl.variables,
        variable_defaults=tpl.variable_defaults,
        status='inactive',
        parent_id=tpl.id,
        sender_name=tpl.sender_name,
        reply_to=tpl.reply_to,
        branding=tpl.branding,
    )
    db.add(copy)
    await db.commit()
    await db.refresh(copy)
    return _template_out(copy)


@router.post('/templates/{template_id}/activate')
async def activate_template(_admin: SuperAdmin, template_id: UUID, db: AsyncSession = Depends(get_db)):
    tpl = await _get_template(db, template_id)
    tpl.status = 'active'
    await db.commit()
    return {'success': True, 'status': 'active'}


@router.post('/templates/{template_id}/deactivate')
async def deactivate_template(_admin: SuperAdmin, template_id: UUID, db: AsyncSession = Depends(get_db)):
    tpl = await _get_template(db, template_id)
    tpl.status = 'inactive'
    await db.commit()
    return {'success': True, 'status': 'inactive'}


@router.delete('/templates/{template_id}')
async def archive_template(_admin: SuperAdmin, template_id: UUID, db: AsyncSession = Depends(get_db)):
    """Soft delete — archives template, never hard deletes."""
    tpl = await _get_template(db, template_id)
    tpl.status = 'archived'
    tpl.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {'success': True, 'status': 'archived'}


@router.post('/templates/preview')
async def preview_template(_admin: SuperAdmin, body: PreviewRequest):
    subject, html, text, missing = render_template(
        body.subject, body.html_body, None, body.variables, strict=False
    )
    return {'subject': subject, 'html': html, 'missing_variables': missing}


async def _get_template(db: AsyncSession, template_id: UUID) -> EmailTemplate:
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id, EmailTemplate.deleted_at.is_(None))
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(404, 'Template not found')
    return tpl


# --- Events ---

@router.get('/events')
async def list_events(_admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailEvent).order_by(EmailEvent.category, EmailEvent.event_key))
    rows = result.scalars().all()
    db_map = {e.event_key: e for e in rows}
    out = []
    for defn in EVENT_REGISTRY:
        row = db_map.get(defn.event_key)
        out.append({
            'event_key': defn.event_key,
            'name': row.name if row else defn.name,
            'category': defn.category,
            'description': defn.description,
            'default_template_slug': defn.default_template_slug,
            'required_variables': list(defn.required_variables),
            'is_enabled': row.is_enabled if row else False,
            'template_id': str(row.template_id) if row and row.template_id else None,
            'id': str(row.id) if row else None,
        })
    return out


@router.patch('/events/{event_key}')
async def update_event(
    _admin: SuperAdmin,
    event_key: str,
    body: EventUpdate,
    db: AsyncSession = Depends(get_db),
):
    if not get_event_definition(event_key):
        raise HTTPException(404, 'Unknown event key')
    result = await db.execute(select(EmailEvent).where(EmailEvent.event_key == event_key))
    row = result.scalar_one_or_none()
    if not row:
        defn = get_event_definition(event_key)
        row = EmailEvent(
            id=uuid4(),
            event_key=event_key,
            name=defn.name,
            category=defn.category,
            description=defn.description,
            is_enabled=body.is_enabled if body.is_enabled is not None else True,
            template_id=body.template_id,
        )
        db.add(row)
    else:
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
    await db.commit()
    return {'success': True, 'event_key': event_key}


@router.post('/dispatch')
async def dispatch_event(_admin: SuperAdmin, body: DispatchRequest, db: AsyncSession = Depends(get_db)):
    dispatcher = EmailDispatcher(db)
    queue_id = await dispatcher.dispatch(body.event_key, body.recipient, body.variables)
    if not queue_id:
        raise HTTPException(400, 'Could not dispatch — event disabled or no active template')
    await db.commit()
    return {'success': True, 'queue_item_id': str(queue_id)}


# --- SMTP / Settings ---

@router.get('/settings/smtp')
async def list_smtp(_admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SmtpConfig).order_by(SmtpConfig.is_primary.desc()))
    configs = []
    for c in result.scalars().all():
        configs.append({
            'id': str(c.id),
            'name': c.name,
            'provider': c.provider,
            'host': c.host,
            'port': c.port,
            'username': c.username,
            'encryption': c.encryption,
            'from_email': c.from_email,
            'from_name': c.from_name,
            'is_primary': c.is_primary,
            'is_fallback': c.is_fallback,
            'is_active': c.is_active,
            'has_password': bool(c.password_encrypted),
            'last_tested_at': c.last_tested_at.isoformat() if c.last_tested_at else None,
            'last_test_status': c.last_test_status,
        })
    return configs


@router.post('/settings/smtp', status_code=201)
async def create_smtp(_admin: SuperAdmin, body: SmtpConfigCreate, db: AsyncSession = Depends(get_db)):
    if body.is_primary:
        await db.execute(
            select(SmtpConfig)  # clear other primaries handled below
        )
        primaries = await db.execute(select(SmtpConfig).where(SmtpConfig.is_primary == True))  # noqa: E712
        for p in primaries.scalars().all():
            p.is_primary = False

    cfg = SmtpConfig(
        id=uuid4(),
        name=body.name,
        provider=body.provider,
        host=body.host,
        port=body.port,
        username=body.username,
        password_encrypted=encrypt_secret(body.password) if body.password else None,
        encryption=body.encryption,
        from_email=body.from_email,
        from_name=body.from_name,
        is_primary=body.is_primary,
        is_fallback=body.is_fallback,
    )
    db.add(cfg)
    await db.commit()
    return {'id': str(cfg.id), 'success': True}


@router.post('/settings/smtp/{config_id}/test')
async def test_smtp(_admin: SuperAdmin, config_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SmtpConfig).where(SmtpConfig.id == config_id))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(404, 'SMTP config not found')
    providers = await get_provider_chain(db)
    test_result, _ = await send_with_fallback(
        providers,
        OutboundEmail(to=cfg.from_email, subject='TenderIQ SMTP Test', html='<p>Connection successful.</p>'),
    )
    cfg.last_tested_at = datetime.now(timezone.utc)
    cfg.last_test_status = 'ok' if test_result.success else 'failed'
    await db.commit()
    return {'success': test_result.success, 'error': test_result.error}


@router.get('/settings/firebase')
async def get_firebase(_admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FirebaseConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        return {'configured': False}
    return {
        'id': str(cfg.id),
        'project_id': cfg.project_id,
        'auth_domain': cfg.auth_domain,
        'app_id': cfg.app_id,
        'reset_url': cfg.reset_url,
        'verify_url': cfg.verify_url,
        'dynamic_link_domain': cfg.dynamic_link_domain,
        'is_enabled': cfg.is_enabled,
        'use_for_auth_emails': cfg.use_for_auth_emails,
        'has_api_key': bool(cfg.api_key_encrypted),
    }


@router.put('/settings/firebase')
async def update_firebase(_admin: SuperAdmin, body: FirebaseConfigUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FirebaseConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = FirebaseConfig(id=uuid4())
        db.add(cfg)
    data = body.model_dump(exclude_unset=True)
    if 'api_key' in data:
        cfg.api_key_encrypted = encrypt_secret(data.pop('api_key')) if data['api_key'] else None
    for k, v in data.items():
        setattr(cfg, k, v)
    await db.commit()
    return {'success': True}


@router.get('/settings/branding')
async def get_branding(_admin: SuperAdmin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailBranding).limit(1))
    b = result.scalar_one_or_none()
    if not b:
        return {}
    return {
        'logo_url': b.logo_url,
        'primary_color': b.primary_color,
        'accent_color': b.accent_color,
        'footer_html': b.footer_html,
        'company_name': b.company_name,
        'support_email': b.support_email,
        'website_url': b.website_url,
        'social_links': b.social_links or {},
    }


@router.put('/settings/branding')
async def update_branding(_admin: SuperAdmin, body: BrandingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailBranding).limit(1))
    b = result.scalar_one_or_none()
    if not b:
        b = EmailBranding(id=uuid4())
        db.add(b)
    for k, v in body.model_dump().items():
        setattr(b, k, v)
    await db.commit()
    return {'success': True}


# --- Test send ---

@router.post('/test-send')
async def test_send(_admin: SuperAdmin, body: TestSendRequest, db: AsyncSession = Depends(get_db)):
    if body.template_id:
        tpl = await _get_template(db, body.template_id)
        subject, html, text, _ = render_template(
            tpl.subject, tpl.html_body, tpl.text_body, body.variables, tpl.variable_defaults
        )
    else:
        subject = body.subject or 'TenderIQ Test'
        html = body.html_body or '<p>Test email</p>'
        text = None

    dispatcher = EmailDispatcher(db)
    qid = await dispatcher.dispatch(
        'admin.system.alert',
        body.to,
        {**body.variables, 'alert_message': subject},
    )
    if not qid:
        providers = await get_provider_chain(db)
        result, provider = await send_with_fallback(
            providers, OutboundEmail(to=body.to, subject=subject, html=html, text=text)
        )
        return {'success': result.success, 'provider': provider, 'message_id': result.message_id}
    await db.commit()
    return {'success': True, 'queued': True, 'queue_item_id': str(qid)}


# --- Logs ---

@router.get('/logs')
async def list_logs(
    _admin: SuperAdmin,
    limit: int = Query(50, le=200),
    offset: int = 0,
    status: Optional[str] = None,
    event_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(EmailLog).order_by(EmailLog.created_at.desc())
    if status:
        q = q.where(EmailLog.status == status)
    if event_name:
        q = q.where(EmailLog.event_name == event_name)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return [
        {
            'id': str(l.id),
            'recipient': l.recipient,
            'template_id': str(l.template_id) if l.template_id else None,
            'event_name': l.event_name,
            'subject': l.subject,
            'status': l.status,
            'retry_count': l.retry_count,
            'provider_name': l.provider_name,
            'message_id': l.message_id,
            'sent_at': l.sent_at.isoformat() if l.sent_at else None,
            'opened_at': l.opened_at.isoformat() if l.opened_at else None,
            'clicked_at': l.clicked_at.isoformat() if l.clicked_at else None,
            'error_message': l.error_message,
            'created_at': l.created_at.isoformat() if l.created_at else None,
        }
        for l in result.scalars().all()
    ]


# --- Queue ---

@router.get('/queue')
async def list_queue(
    _admin: SuperAdmin,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(EmailQueueItem).order_by(EmailQueueItem.created_at.desc()).limit(limit)
    if status:
        q = q.where(EmailQueueItem.status == status)
    result = await db.execute(q)
    return [
        {
            'id': str(i.id),
            'recipient': i.recipient,
            'event_name': i.event_name,
            'status': i.status,
            'retry_count': i.retry_count,
            'max_retries': i.max_retries,
            'next_retry_at': i.next_retry_at.isoformat() if i.next_retry_at else None,
            'error_message': i.error_message,
            'created_at': i.created_at.isoformat() if i.created_at else None,
        }
        for i in result.scalars().all()
    ]


@router.post('/queue/{item_id}/retry')
async def retry_queue_item(_admin: SuperAdmin, item_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailQueueItem).where(EmailQueueItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, 'Queue item not found')
    item.status = 'pending'
    item.retry_count = 0
    item.next_retry_at = None
    await db.commit()
    from ...core.tasks.inline import schedule_job

    schedule_job('email_process', _job_id=str(item.id), queue_item_id=str(item.id))
    return {'success': True}


# --- Analytics ---

@router.get('/analytics')
async def email_analytics(_admin: SuperAdmin, days: int = Query(30, le=365), db: AsyncSession = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(select(EmailLog).where(EmailLog.created_at >= since))
    logs = result.scalars().all()
    total = len(logs)
    sent = sum(1 for l in logs if l.status in ('sent', 'delivered'))
    failed = sum(1 for l in logs if l.status in ('failed', 'dead_letter'))
    retrying = sum(1 for l in logs if l.status == 'retrying')
    opened = sum(1 for l in logs if l.opened_at)
    clicked = sum(1 for l in logs if l.clicked_at)

    queue_result = await db.execute(select(EmailQueueItem))
    queue_items = queue_result.scalars().all()
    pending = sum(1 for q in queue_items if q.status == 'pending')
    processing = sum(1 for q in queue_items if q.status == 'processing')

    return {
        'period_days': days,
        'total': total,
        'sent': sent,
        'failed': failed,
        'retrying': retrying,
        'delivery_rate': round(sent / total * 100, 2) if total else 0,
        'failure_rate': round(failed / total * 100, 2) if total else 0,
        'open_rate': round(opened / sent * 100, 2) if sent else 0,
        'click_rate': round(clicked / sent * 100, 2) if sent else 0,
        'queue_pending': pending,
        'queue_processing': processing,
        'by_status': _count_by(logs, 'status'),
        'by_event': _count_by(logs, 'event_name'),
    }


def _count_by(logs: list, attr: str) -> dict:
    out: dict[str, int] = {}
    for l in logs:
        key = getattr(l, attr, None) or 'unknown'
        out[key] = out.get(key, 0) + 1
    return out


# --- Public auth endpoints (no super admin) ---

@router.post('/auth/forgot-password')
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = PasswordResetService(db)
    await service.request_reset(
        body.email,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent'),
    )
    return {'success': True, 'message': 'If an account exists, a reset link has been sent.'}


@router.post('/auth/reset-password')
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    service = PasswordResetService(db)
    email = await service.validate_token(body.token)
    if not email:
        raise HTTPException(400, 'Invalid or expired reset token')
    if not await service.apply_new_password(email, body.new_password):
        raise HTTPException(400, 'No account found for this email')
    ok = await service.consume_token(body.token)
    if not ok:
        raise HTTPException(400, 'Unable to reset password')
    return {'success': True, 'message': 'Password updated successfully'}
