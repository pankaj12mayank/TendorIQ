"""Email API Router"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field

from ...core.email.service import EmailService, get_email_service, EmailTriggerHandler, get_trigger_handler
from ...core.email.schemas import (
    EmailRequest, 
    EmailResponse, 
    EmailType, 
    EmailStatus,
    EmailLog,
    EmailBatchRequest,
    EmailStats
)

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
    user_email: str
    data: dict


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


MOCK_LOGS = []


@router.post('/send', response_model=EmailResponse)
async def send_email(
    request: SendEmailRequest,
    service: EmailService = Depends(get_email_service),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...),
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
        
        log = EmailLog(
            tenant_id=UUID(x_tenant_id),
            user_id=UUID(x_user_id) if x_user_id else None,
            email_type=request.template_type or EmailType.GENERIC,
            to_address=', '.join(request.to) if isinstance(request.to, list) else request.to,
            from_email='noreply@tenderiq.com',
            subject=request.subject,
            status=result.status,
            message_id=result.message_id,
            sent_at=result.sent_at
        )
        MOCK_LOGS.append(log)
        
        return result
    except Exception as e:
        logger.error(f'Failed to send email: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/send/batch', response_model=list[EmailResponse])
async def send_batch_emails(
    request: EmailBatchRequest,
    service: EmailService = Depends(get_email_service),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...),
):
    """Send multiple emails in batch"""
    results = await service.send_batch(request.emails)
    return results


@router.post('/trigger/upload-received')
async def trigger_upload_received(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
):
    """Trigger upload received email"""
    result = await handler.handle_upload_received(
        user_email=request.data.get('user_email', request.user_email),
        file_name=request.data.get('file_name'),
        tender_name=request.data.get('tender_name')
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/processing-completed')
async def trigger_processing_completed(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
):
    """Trigger processing completed email"""
    result = await handler.handle_processing_completed(
        user_email=request.data.get('user_email', request.user_email),
        file_name=request.data.get('file_name'),
        tender_name=request.data.get('tender_name')
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/processing-failed')
async def trigger_processing_failed(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
):
    """Trigger processing failed email"""
    result = await handler.handle_processing_failed(
        user_email=request.data.get('user_email', request.user_email),
        file_name=request.data.get('file_name'),
        error=request.data.get('error', 'Unknown error')
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/quota-exceeded')
async def trigger_quota_exceeded(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
):
    """Trigger quota exceeded email"""
    result = await handler.handle_quota_exceeded(
        user_email=request.data.get('user_email', request.user_email),
        feature=request.data.get('feature'),
        used=request.data.get('used', 0),
        limit=request.data.get('limit', 0)
    )
    return {'success': True, 'message_id': result.message_id}


@router.post('/trigger/subscription-alert')
async def trigger_subscription_alert(
    request: TriggerRequest,
    handler: EmailTriggerHandler = Depends(get_trigger_handler),
):
    """Trigger subscription alert email"""
    result = await handler.handle_subscription_alert(
        user_email=request.data.get('user_email', request.user_email),
        alert_type=request.data.get('alert_type'),
        message=request.data.get('message')
    )
    return {'success': True, 'message_id': result.message_id}


@router.get('/logs', response_model=list[EmailLogResponse])
async def get_email_logs(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status: Optional[EmailStatus] = None,
    email_type: Optional[EmailType] = None,
    x_tenant_id: str = Header(...),
):
    """Get email sending logs"""
    logs = MOCK_LOGS
    
    if status:
        logs = [l for l in logs if l.status == status]
    if email_type:
        logs = [l for l in logs if l.email_type == email_type]
    
    return [
        EmailLogResponse(
            id=str(log.id),
            email_type=log.email_type.value,
            to_address=log.to_address,
            subject=log.subject,
            status=log.status.value,
            sent_at=log.sent_at.isoformat() if log.sent_at else None,
            created_at=log.created_at.isoformat()
        )
        for log in logs[offset:offset+limit]
    ]


@router.get('/stats', response_model=EmailStatsResponse)
async def get_email_stats(
    days: int = Query(30, le=365),
    x_tenant_id: str = Header(...),
):
    """Get email statistics"""
    logs = MOCK_LOGS
    
    total_sent = len([l for l in logs if l.status == EmailStatus.SENT])
    total_delivered = len([l for l in logs if l.status == EmailStatus.DELIVERED])
    total_failed = len([l for l in logs if l.status == EmailStatus.FAILED])
    
    by_type = {}
    for log in logs:
        key = log.email_type.value
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