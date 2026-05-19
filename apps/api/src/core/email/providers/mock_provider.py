"""Development mock provider — logs emails without sending."""

import asyncio
import logging
from datetime import datetime

from .base import EmailProvider, OutboundEmail, SendResult

logger = logging.getLogger(__name__)


class MockProvider(EmailProvider):
    name = 'mock'

    async def send(self, email: OutboundEmail) -> SendResult:
        await asyncio.sleep(0.05)
        to = email.to if isinstance(email.to, list) else [email.to]
        logger.info('[MOCK EMAIL] to=%s subject=%s', to, email.subject)
        return SendResult(
            success=True,
            message_id=f'mock-{datetime.utcnow().timestamp()}',
            provider=self.name,
        )

    async def test_connection(self) -> SendResult:
        return SendResult(success=True, provider=self.name, message_id='mock-ok')
