"""Event-driven email dispatcher — queues emails in DB, sends in-process."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import EmailEvent, EmailLog, EmailQueueItem, EmailTemplate
from ..events.registry import get_event_definition
from ..renderers.template_renderer import render_template
from ...config import settings
from ...queue.config import QueueConfig
from ...tasks.inline import schedule_job

logger = logging.getLogger(__name__)


class EmailDispatcher:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def dispatch(
        self,
        event_key: str,
        recipient: str,
        variables: dict[str, Any],
        tenant_id: Optional[UUID] = None,
        priority: int = 5,
        scheduled_at: Optional[datetime] = None,
    ) -> Optional[UUID]:
        event_def = get_event_definition(event_key)
        if not event_def:
            logger.warning('Unknown email event: %s', event_key)
            return None

        event_row = await self._resolve_event(event_key, tenant_id)
        if event_row and not event_row.is_enabled:
            logger.info('Event disabled: %s', event_key)
            return None

        template = await self._resolve_template(event_row, event_def.default_template_slug, tenant_id)
        if not template:
            logger.warning('No template for event %s', event_key)
            return None
        if template.status != 'active':
            logger.info('Template inactive for event %s (slug=%s)', event_key, template.slug)
            return None

        defaults = {
            'company_name': 'TenderIQ',
            'dashboard_link': f'{settings.FRONTEND_URL}/dashboard',
            'billing_link': f'{settings.FRONTEND_URL}/dashboard/billing',
            'support_email': 'support@tenderiq.com',
            **(template.variable_defaults or {}),
        }
        subject, html, text, missing = render_template(
            template.subject,
            template.html_body,
            template.text_body,
            variables,
            defaults,
            strict=False,
        )
        if missing:
            logger.warning('Email %s missing variables: %s', event_key, missing)

        log = EmailLog(
            tenant_id=tenant_id,
            recipient=recipient,
            template_id=template.id,
            event_name=event_key,
            subject=subject,
            status='queued',
            log_meta={'variables': variables, 'missing': missing},
        )
        self.db.add(log)
        await self.db.flush()

        queue_item = EmailQueueItem(
            tenant_id=tenant_id,
            recipient=recipient,
            template_id=template.id,
            event_name=event_key,
            subject=subject,
            html_body=html,
            variables={**variables, '_text': text},
            status='pending',
            max_retries=QueueConfig.MAX_RETRIES,
            scheduled_at=scheduled_at or datetime.now(timezone.utc),
            priority=priority,
            log_id=log.id,
        )
        self.db.add(queue_item)
        await self.db.flush()

        schedule_job(
            'email_process',
            _job_id=str(queue_item.id),
            queue_item_id=str(queue_item.id),
        )
        return queue_item.id

    async def _resolve_event(self, event_key: str, tenant_id: Optional[UUID]) -> Optional[EmailEvent]:
        q = select(EmailEvent).where(EmailEvent.event_key == event_key)
        if tenant_id:
            q = q.where((EmailEvent.tenant_id == tenant_id) | (EmailEvent.tenant_id.is_(None)))
        else:
            q = q.where(EmailEvent.tenant_id.is_(None))
        result = await self.db.execute(q.limit(1))
        return result.scalar_one_or_none()

    async def _resolve_template(
        self,
        event_row: Optional[EmailEvent],
        default_slug: str,
        tenant_id: Optional[UUID],
    ) -> Optional[EmailTemplate]:
        if event_row and event_row.template_id:
            result = await self.db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.id == event_row.template_id,
                    EmailTemplate.deleted_at.is_(None),
                )
            )
            tpl = result.scalar_one_or_none()
            if tpl:
                return tpl

        q = select(EmailTemplate).where(
            EmailTemplate.slug == default_slug,
            EmailTemplate.deleted_at.is_(None),
        )
        if tenant_id:
            q = q.where((EmailTemplate.tenant_id == tenant_id) | (EmailTemplate.tenant_id.is_(None)))
        else:
            q = q.where(EmailTemplate.tenant_id.is_(None))
        q = q.order_by(EmailTemplate.tenant_id.desc().nullslast())
        result = await self.db.execute(q.limit(1))
        return result.scalar_one_or_none()
