"""Email API Router"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, model_validator

from ...core.auth import AuthContext
from ...core.email.service import EmailService, get_email_service, EmailTriggerHandler, get_trigger_handler
from ...core.email.schemas import (
    EmailRequest, 
    EmailResponse, 
    EmailType, 
    EmailStatus,
    EmailBatchRequest,
    EmailStats
)
from ..dependencies.auth import get_current_user
from ...core.database import get_db
from ...core.email.db_models import EmailLog as DbEmailLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/emails', tags=['Email'])


class SendEmailRequest(BaseModel):
    to: str | list[str]
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    template_type: Optional[EmailType] = None
    template_data: Optional[dict] = None
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    attachments: Optional[list[dict]] = None


class TriggerRequest(BaseModel):
    user_email: str = ''
    data: dict = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def accept_flat_or_nested_body(cls, value):
        if not isinstance(value, dict):
            return value
        if 'data' in value and isinstance(value.get('data'), dict):
            return {
                'user_email': value.get('user_email', ''),
                'data': value['data'],
            }
        email = value.get('user_email', '')
        data = {k: v for k, v in value.items() if k != 'user_email'}
        return {'user_email': email, 'data': data}


class EmailLogResponse(BaseModel):
    id: str
    email_type: str
    to_address: str
    subject: str
    status: str
    sent_at: Optional[str]
    created_at: str


class EmailStatsResponse(BaseModel):
    total_sent: int
    total_delivered: int
    total_failed: int
    by_type: dict


async def _persist_email_log(
    db: AsyncSession,
    *,
    tenant_id: str | None,
    recipient: str,
    subject: str,
    event_name: str,
    status: str,
    message_id: str | None = None,
) -> DbEmailLog:
    log = DbEmailLog(
        tenant_id=UUID(tenant_id) if tenant_id else None,
        recipient=recipient,
        event_name=event_name,
        subject=subject,
        status=status,
        message_id=message_id,
        sent_at=datetime.utcnow() if status == EmailStatus.SENT.value else None,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.post('/send', response_model=EmailResponse)
async def send_email(
    request: SendEmailRequest,
    service: EmailService = Depends(get_email_service),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a single email"""
    try:
        email_req = EmailRequest(
            to=request.to,
            subject=request.subject,
            html=request.html,
            text=request.text,
            template_type=request.template_type,
            template_data=request.template_data,
            cc=request.cc,
            bcc=request.bcc,
            attachments=request.attachments
        )
        
        result = await service.send(email_req)
        to_address = ', '.join(request.to) if isinstance(request.to, list) else request.to
        await _persist_email_log(
            db,
            tenant_id=current_user.tenant_id,
            recipient=to_address,
            subject=request.subject,
            event_name=(request.template_type or EmailType.GENERIC).value,
            status=result.status.value if hasattr(result.status, 'value') else str(result.status),
            message_id=result.message_id,
        )
        
        return result
    except Exception as e:
        logger.error(f'Failed to send email: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/send/batch', response_model=list[EmailResponse])
async def send_batch_emails(
    request: EmailBatchRequest,
    service: EmailService = Depends(get_email_service),
    current_user: AuthContext = Depends(get_current_user),
):
    """Send multiple emails in batch"""
    results = await service.send_batch(request.emails)
    return results


@router.post('/trigger/upload-received')
async def trigger_upload_received(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger upload received email"""
    user_email = request.data.get('user_email') or request.user_email
    result = await handler.handle_upload_received(
        user_email=user_email,
        file_name=request.data.get('file_name'),
        tender_name=request.data.get('tender_name')
    )
    await _persist_email_log(
        db,
        tenant_id=current_user.tenant_id,
        recipient=user_email,
        subject='Upload received',
        event_name=EmailType.UPLOAD_RECEIVED.value,
        status=EmailStatus.SENT.value,
        message_id=result.message_id,
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/processing-completed')
async def trigger_processing_completed(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger processing completed email"""
    user_email = request.data.get('user_email') or request.user_email
    result = await handler.handle_processing_completed(
        user_email=user_email,
        file_name=request.data.get('file_name'),
        tender_name=request.data.get('tender_name')
    )
    await _persist_email_log(
        db,
        tenant_id=current_user.tenant_id,
        recipient=user_email,
        subject='Processing completed',
        event_name=EmailType.PROCESSING_COMPLETED.value,
        status=EmailStatus.SENT.value,
        message_id=result.message_id,
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/processing-failed')
async def trigger_processing_failed(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger processing failed email"""
    user_email = request.data.get('user_email') or request.user_email
    result = await handler.handle_processing_failed(
        user_email=user_email,
        file_name=request.data.get('file_name'),
        error=request.data.get('error', 'Unknown error')
    )
    await _persist_email_log(
        db,
        tenant_id=current_user.tenant_id,
        recipient=user_email,
        subject='Processing failed',
        event_name=EmailType.PROCESSING_FAILED.value,
        status=EmailStatus.SENT.value,
        message_id=result.message_id,
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/quota-exceeded')
async def trigger_quota_exceeded(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger quota exceeded email"""
    user_email = request.data.get('user_email') or request.user_email
    result = await handler.handle_quota_exceeded(
        user_email=user_email,
        feature=request.data.get('feature'),
        used=request.data.get('used', 0),
        limit=request.data.get('limit', 0)
    )
    await _persist_email_log(
        db,
        tenant_id=current_user.tenant_id,
        recipient=user_email,
        subject='Quota exceeded',
        event_name=EmailType.QUOTA_EXCEEDED.value,
        status=EmailStatus.SENT.value,
        message_id=result.message_id,
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/subscription-alert')
async def trigger_subscription_alert(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger subscription alert email"""
    user_email = request.data.get('user_email') or request.user_email
    result = await handler.handle_subscription_alert(
        user_email=user_email,
        alert_type=request.data.get('alert_type'),
        message=request.data.get('message')
    )
    await _persist_email_log(
        db,
        tenant_id=current_user.tenant_id,
        recipient=user_email,
        subject='Subscription alert',
        event_name=EmailType.SUBSCRIPTION_ALERT.value,
        status=EmailStatus.SENT.value,
        message_id=result.message_id,
    )
    return {'success': True, 'message_id': result.message_id}


@router.get('/logs', response_model=list[EmailLogResponse])
async def get_email_logs(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status: Optional[EmailStatus] = None,
    email_type: Optional[EmailType] = None,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get email sending logs"""
    conditions = []
    if current_user.tenant_id:
        conditions.append(DbEmailLog.tenant_id == UUID(current_user.tenant_id))
    if status:
        conditions.append(DbEmailLog.status == status.value)
    if email_type:
        conditions.append(DbEmailLog.event_name == email_type.value)

    q = select(DbEmailLog).order_by(DbEmailLog.created_at.desc())
    if conditions:
        q = q.where(*conditions)
    q = q.offset(offset).limit(limit)
    rows = (await db.execute(q)).scalars().all()

    return [
        EmailLogResponse(
            id=str(log.id),
            email_type=log.event_name or EmailType.GENERIC.value,
            to_address=log.recipient,
            subject=log.subject,
            status=log.status,
            sent_at=log.sent_at.isoformat() if log.sent_at else None,
            created_at=log.created_at.isoformat() if log.created_at else datetime.utcnow().isoformat(),
        )
        for log in rows
    ]


@router.get('/stats', response_model=EmailStatsResponse)
async def get_email_stats(
    days: int = Query(30, le=365),
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get email statistics"""
    conditions = []
    if current_user.tenant_id:
        conditions.append(DbEmailLog.tenant_id == UUID(current_user.tenant_id))

    base = select(DbEmailLog)
    if conditions:
        base = base.where(*conditions)
    rows = (await db.execute(base)).scalars().all()

    total_sent = len([l for l in rows if l.status == EmailStatus.SENT.value])
    total_delivered = len([l for l in rows if l.status == EmailStatus.DELIVERED.value])
    total_failed = len([l for l in rows if l.status == EmailStatus.FAILED.value])

    by_type: dict[str, int] = {}
    for log in rows:
        key = log.event_name or EmailType.GENERIC.value
        by_type[key] = by_type.get(key, 0) + 1

    return EmailStatsResponse(
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_failed=total_failed,
        by_type=by_type
    )


@router.get('/templates')
async def list_templates():
    """List available email templates"""
    from ...core.email.templates import get_all_templates
    templates = get_all_templates()
    return [
        {
            'template_id': t.template_id,
            'name': t.name,
            'subject': t.subject,
            'type': t.email_type.value
        }
        for t in templates
    ]