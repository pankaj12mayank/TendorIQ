"""Resend API email provider."""

import logging
import os
from typing import Optional

from .base import EmailProvider, OutboundEmail, SendResult

logger = logging.getLogger(__name__)

try:
    import resend
except ImportError:
    resend = None


class ResendProvider(EmailProvider):
    name = 'resend'

    def __init__(self, api_key: Optional[str] = None, from_email: str = 'noreply@tenderiq.com', from_name: str = 'TenderIQ'):
        self.api_key = api_key or os.environ.get('RESEND_API_KEY') or os.environ.get('EMAIL_API_KEY', '')
        self.from_email = from_email
        self.from_name = from_name
        if resend and self.api_key:
            resend.api_key = self.api_key

    async def send(self, email: OutboundEmail) -> SendResult:
        if not resend or not self.api_key:
            return SendResult(success=False, provider=self.name, error='Resend not configured')

        try:
            from_addr = email.from_email or f'{self.from_name} <{self.from_email}>'
            params = {
                'from': from_addr,
                'to': email.to if isinstance(email.to, list) else [email.to],
                'subject': email.subject,
                'html': email.html,
            }
            if email.text:
                params['text'] = email.text
            if email.reply_to:
                params['reply_to'] = email.reply_to

            response = resend.Emails.send(params)
            return SendResult(success=True, message_id=response.get('id'), provider=self.name)
        except Exception as exc:
            logger.exception('Resend send failed')
            return SendResult(success=False, provider=self.name, error=str(exc))

    async def test_connection(self) -> SendResult:
        if resend and self.api_key:
            return SendResult(success=True, provider=self.name, message_id='resend-configured')
        return SendResult(success=False, provider=self.name, error='Resend API key missing')
