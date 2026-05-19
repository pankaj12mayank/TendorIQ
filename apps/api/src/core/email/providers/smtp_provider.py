"""SMTP email provider with TLS/SSL support."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base import EmailProvider, OutboundEmail, SendResult

logger = logging.getLogger(__name__)


class SmtpProvider(EmailProvider):
    name = 'smtp'

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str,
        encryption: str = 'tls',
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.encryption = encryption

    def _build_message(self, email: OutboundEmail) -> MIMEMultipart:
        msg = MIMEMultipart('alternative')
        from_addr = email.from_email or self.from_email
        from_label = email.from_name or self.from_name
        msg['Subject'] = email.subject
        msg['From'] = f'{from_label} <{from_addr}>'
        recipients = email.to if isinstance(email.to, list) else [email.to]
        msg['To'] = ', '.join(recipients)
        if email.reply_to:
            msg['Reply-To'] = email.reply_to
        if email.text:
            msg.attach(MIMEText(email.text, 'plain'))
        msg.attach(MIMEText(email.html, 'html'))
        return msg

    async def send(self, email: OutboundEmail) -> SendResult:
        try:
            msg = self._build_message(email)
            recipients = email.to if isinstance(email.to, list) else [email.to]

            if self.encryption == 'ssl':
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=30)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=30)
                if self.encryption == 'tls':
                    server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)
            server.sendmail(self.from_email, recipients, msg.as_string())
            server.quit()
            return SendResult(success=True, message_id=f'smtp-{hash(email.subject)}', provider=self.name)
        except Exception as exc:
            logger.exception('SMTP send failed')
            return SendResult(success=False, provider=self.name, error=str(exc))

    async def test_connection(self) -> SendResult:
        try:
            if self.encryption == 'ssl':
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=15)
                if self.encryption == 'tls':
                    server.starttls()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.quit()
            return SendResult(success=True, provider=self.name, message_id='connection-ok')
        except Exception as exc:
            return SendResult(success=False, provider=self.name, error=str(exc))
