"""Email Service with Resend Provider"""

import logging
from typing import Optional, Any
from datetime import datetime, timedelta
from enum import Enum
try:
    import resend
    from resend.exceptions import ResendError
except ImportError:
    resend = None

    class ResendError(Exception):
        pass

from .templates import EmailTemplate, get_template, TEMPLATES
from .schemas import EmailRequest, EmailResponse, EmailStatus, EmailType

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    RESEND = 'resend'
    SENDGRID = 'sendgrid'
    SMTP = 'smtp'


class EmailService:
    def __init__(self, provider: EmailProvider = EmailProvider.RESEND):
        self.provider = provider
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        if self.provider == EmailProvider.RESEND:
            if resend is None:
                logger.warning('resend package not installed, email service will run in mock mode')
                return
            api_key = getattr(__import__('os').environ, 'RESEND_API_KEY', None)
            if api_key:
                resend.api_key = api_key
                self._client = resend
                logger.info('Resend email client initialized')
            else:
                logger.warning('RESEND_API_KEY not found, email service will run in mock mode')

    async def send(self, request: EmailRequest) -> EmailResponse:
        start_time = datetime.utcnow()
        
        try:
            if self._client:
                result = await self._send_via_resend(request)
            else:
                result = await self._send_mock(request)
            
            return EmailResponse(
                message_id=result.get('message_id', f'mock_{datetime.utcnow().timestamp()}'),
                status=EmailStatus.SENT,
                sent_at=datetime.utcnow(),
                provider=self.provider.value,
                metadata=result
            )
        except Exception as e:
            logger.error(f'Failed to send email: {str(e)}')
            return EmailResponse(
                message_id=f'failed_{datetime.utcnow().timestamp()}',
                status=EmailStatus.FAILED,
                error=str(e)
            )

    async def _send_via_resend(self, request: EmailRequest) -> dict:
        template = get_template(request.template_type) if request.template_type else None
        
        html_content = request.html
        if template and request.template_data:
            html_content = self._render_template(template, request.template_data)
        
        params = {
            'from': request.from_email or 'TenderIQ <noreply@tenderiq.com>',
            'to': request.to,
            'subject': request.subject,
            'html': html_content,
            'text': request.text or request.subject,
        }
        
        if request.cc:
            params['cc'] = request.cc
        if request.bcc:
            params['bcc'] = request.bcc
        if request.reply_to:
            params['reply_to'] = request.reply_to
        if request.attachments:
            params['attachments'] = request.attachments

        response = self._client.Emails.send(params)
        return {'message_id': response.get('id'), 'provider': 'resend'}

    async def _send_mock(self, request: EmailRequest) -> dict:
        await self._simulate_delay()
        logger.info(f'[MOCK] Email sent to {request.to}: {request.subject}')
        return {
            'message_id': f'mock_{datetime.utcnow().timestamp()}',
            'provider': 'mock',
            'to': request.to,
            'subject': request.subject
        }

    async def _simulate_delay(self):
        import asyncio
        await asyncio.sleep(0.1)

    def _render_template(self, template: EmailTemplate, data: dict) -> str:
        content = template.html_content
        for key, value in data.items():
            placeholder = f'{{{{{key}}}}}'
            content = content.replace(placeholder, str(value))
        return content

    async def send_batch(self, requests: list[EmailRequest]) -> list[EmailResponse]:
        results = []
        for request in requests:
            result = await self.send(request)
            results.append(result)
        return results


email_service = EmailService()


def get_email_service() -> EmailService:
    return email_service


class EmailTriggerHandler:
    """Handle different email triggers"""

    def __init__(self, email_service: EmailService = None):
        self.email_service = email_service or email_service

    async def handle_upload_received(self, user_email: str, file_name: str, tender_name: str) -> EmailResponse:
        template_data = {
            'file_name': file_name,
            'tender_name': tender_name,
            'timestamp': datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')
        }
        
        request = EmailRequest(
            to=user_email,
            subject=f'File Received: {file_name}',
            template_type=EmailType.UPLOAD_RECEIVED,
            template_data=template_data
        )
        return await self.email_service.send(request)

    async def handle_processing_completed(self, user_email: str, file_name: str, tender_name: str) -> EmailResponse:
        template_data = {
            'file_name': file_name,
            'tender_name': tender_name,
            'timestamp': datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')
        }
        
        request = EmailRequest(
            to=user_email,
            subject=f'Processing Complete: {file_name}',
            template_type=EmailType.PROCESSING_COMPLETED,
            template_data=template_data
        )
        return await self.email_service.send(request)

    async def handle_processing_failed(self, user_email: str, file_name: str, error: str) -> EmailResponse:
        template_data = {
            'file_name': file_name,
            'error': error,
            'support_email': 'support@tenderiq.com',
            'timestamp': datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')
        }
        
        request = EmailRequest(
            to=user_email,
            subject=f'Processing Failed: {file_name}',
            template_type=EmailType.PROCESSING_FAILED,
            template_data=template_data
        )
        return await self.email_service.send(request)

    async def handle_quota_exceeded(self, user_email: str, feature: str, used: int, limit: int) -> EmailResponse:
        template_data = {
            'feature': feature,
            'used': used,
            'limit': limit,
            'upgrade_url': 'https://tenderiq.com/billing',
            'timestamp': datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')
        }
        
        request = EmailRequest(
            to=user_email,
            subject=f'Quota Alert: {feature} limit reached',
            template_type=EmailType.QUOTA_EXCEEDED,
            template_data=template_data
        )
        return await self.email_service.send(request)

    async def handle_subscription_alert(self, user_email: str, alert_type: str, message: str) -> EmailResponse:
        template_data = {
            'alert_type': alert_type,
            'message': message,
            'billing_url': 'https://tenderiq.com/billing',
            'timestamp': datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')
        }
        
        request = EmailRequest(
            to=user_email,
            subject=f'Subscription Alert: {alert_type}',
            template_type=EmailType.SUBSCRIPTION_ALERT,
            template_data=template_data
        )
        return await self.email_service.send(request)


trigger_handler = EmailTriggerHandler()


def get_trigger_handler() -> EmailTriggerHandler:
    return trigger_handler