"""Process queued emails with retry and provider fallback."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import EmailLog, EmailQueueItem
from ..providers.base import OutboundEmail
from ..providers.factory import get_provider_chain, send_with_fallback
from ..services.dispatcher import EmailDispatcher
from ...queue.config import QueueConfig

logger = logging.getLogger(__name__)


class EmailProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_queue_item(self, queue_item_id: str) -> dict:
        result = await self.db.execute(
            select(EmailQueueItem).where(EmailQueueItem.id == UUID(queue_item_id))
        )
        item = result.scalar_one_or_none()
        if not item:
            return {'success': False, 'error': 'Queue item not found'}

        if item.status in ('sent', 'dead_letter'):
            return {'success': True, 'skipped': True}

        now = datetime.now(timezone.utc)
        if item.next_retry_at and item.next_retry_at > now:
            return {'success': False, 'error': 'Not yet time to retry', 'retry_at': item.next_retry_at.isoformat()}

        item.status = 'processing'
        await self.db.flush()

        text = (item.variables or {}).pop('_text', None) if item.variables else None
        outbound = OutboundEmail(
            to=item.recipient,
            subject=item.subject or 'Notification from TenderIQ',
            html=item.html_body or '<p>No content</p>',
            text=text,
        )

        providers = await get_provider_chain(self.db, str(item.tenant_id) if item.tenant_id else None)
        send_result, provider_name = await send_with_fallback(providers, outbound)

        log = None
        if item.log_id:
            log_result = await self.db.execute(select(EmailLog).where(EmailLog.id == item.log_id))
            log = log_result.scalar_one_or_none()

        if send_result.success:
            item.status = 'sent'
            item.provider_name = provider_name
            item.processed_at = now
            item.error_message = None
            if log:
                log.status = 'sent'
                log.provider_name = provider_name
                log.message_id = send_result.message_id
                log.sent_at = now
                log.retry_count = item.retry_count
            await self.db.commit()
            return {'success': True, 'message_id': send_result.message_id, 'provider': provider_name}

        item.retry_count += 1
        item.error_message = send_result.error
        delay = QueueConfig.RETRY_DELAYS.get(item.retry_count)

        if item.retry_count > item.max_retries:
            item.status = 'dead_letter'
            if log:
                log.status = 'failed'
                log.error_message = send_result.error
                log.retry_count = item.retry_count
            await self._notify_admin_failure(item)
        else:
            item.status = 'retry'
            item.next_retry_at = now + timedelta(seconds=delay or 600)
            if log:
                log.status = 'retrying'
                log.retry_count = item.retry_count
                log.error_message = send_result.error

        await self.db.commit()
        return {
            'success': False,
            'error': send_result.error,
            'retry_count': item.retry_count,
            'next_retry_at': item.next_retry_at.isoformat() if item.next_retry_at else None,
        }

    async def _notify_admin_failure(self, item: EmailQueueItem) -> None:
        """Notify super admins when email permanently fails."""
        from ...config import settings

        try:
            dispatcher = EmailDispatcher(self.db)
            await dispatcher.dispatch(
                'admin.system.alert',
                settings.SUPER_ADMIN_EMAIL,
                {
                    'alert_message': f'Email failed for {item.recipient}: {item.error_message}',
                },
            )
        except Exception as exc:
            logger.warning('Admin failure notification skipped: %s', exc)
        logger.error(
            'Email dead-letter: event=%s recipient=%s error=%s',
            item.event_name,
            item.recipient,
            item.error_message,
        )
