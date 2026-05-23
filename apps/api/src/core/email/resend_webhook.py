"""Apply Resend (Svix) webhook events to email_logs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import EmailLog

logger = logging.getLogger(__name__)

_STATUS_BY_TYPE = {
    'email.sent': 'sent',
    'email.delivered': 'delivered',
    'email.delivery_delayed': 'delivery_delayed',
    'email.bounced': 'bounced',
    'email.complained': 'complained',
    'email.failed': 'failed',
}


def _message_id_from_payload(payload: dict[str, Any]) -> Optional[str]:
    data = payload.get('data') or {}
    for key in ('email_id', 'id', 'message_id'):
        raw = data.get(key)
        if raw:
            return str(raw)
    return None


def _parse_webhook_time(payload: dict[str, Any]) -> datetime:
    raw = payload.get('created_at') or (payload.get('data') or {}).get('created_at')
    if raw:
        try:
            normalized = str(raw).replace('Z', '+00:00')
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


async def apply_resend_webhook_event(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    """Update EmailLog rows from a Resend webhook payload."""
    event_type = str(payload.get('type') or '')
    message_id = _message_id_from_payload(payload)
    if not message_id:
        logger.info('Resend webhook ignored (no message id)', type=event_type)
        return {'handled': False, 'reason': 'no_message_id', 'type': event_type}

    result = await db.execute(select(EmailLog).where(EmailLog.message_id == message_id).limit(1))
    log = result.scalar_one_or_none()
    if not log:
        logger.info('Resend webhook: no EmailLog for message_id', message_id=message_id, type=event_type)
        return {'handled': False, 'reason': 'log_not_found', 'type': event_type, 'message_id': message_id}

    when = _parse_webhook_time(payload)
    data = payload.get('data') or {}
    meta = dict(log.log_meta or {})

    if event_type == 'email.opened':
        if not log.opened_at:
            log.opened_at = when
        meta['resend_last_event'] = event_type
        log.log_meta = meta
        await db.commit()
        return {'handled': True, 'type': event_type, 'log_id': str(log.id)}

    if event_type == 'email.clicked':
        if not log.clicked_at:
            log.clicked_at = when
        meta['resend_last_event'] = event_type
        log.log_meta = meta
        await db.commit()
        return {'handled': True, 'type': event_type, 'log_id': str(log.id)}

    new_status = _STATUS_BY_TYPE.get(event_type)
    if new_status:
        log.status = new_status
        if new_status in ('sent', 'delivered') and not log.sent_at:
            log.sent_at = when
        if new_status in ('bounced', 'complained', 'failed'):
            log.error_message = (
                data.get('bounce', {}).get('message')
                or data.get('failed', {}).get('reason')
                or data.get('error')
                or event_type
            )
        meta['resend_last_event'] = event_type
        log.log_meta = meta
        await db.commit()
        return {'handled': True, 'type': event_type, 'log_id': str(log.id), 'status': new_status}

    logger.info('Resend webhook type not mapped', type=event_type)
    return {'handled': False, 'reason': 'unmapped_type', 'type': event_type}
