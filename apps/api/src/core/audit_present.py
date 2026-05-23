"""Shared audit log serialization (tenant + platform APIs)."""

import csv
import io
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog, User


async def load_users_by_id(db: AsyncSession, user_ids: set[UUID]) -> dict[UUID, User]:
    if not user_ids:
        return {}
    rows = (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
    return {u.id: u for u in rows}


def audit_log_to_dict(log: AuditLog, user: Optional[User] = None) -> dict[str, Any]:
    return {
        'id': str(log.id),
        'action': log.action,
        'action_type': log.action_type,
        'resource_type': log.resource_type,
        'resource_id': str(log.resource_id) if log.resource_id else None,
        'resource_name': log.resource_name,
        'user_id': str(log.user_id) if log.user_id else '',
        'user_name': (user.name if user and user.name else '') or '',
        'user_email': (user.email if user else '') or '',
        'user_role': (user.role if user else '') or '',
        'tenant_id': str(log.tenant_id) if log.tenant_id else '',
        'changes': log.changes or {},
        'old_values': log.old_values or {},
        'new_values': log.new_values or {},
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'request_id': log.request_id,
        'created_at': log.created_at.isoformat() if log.created_at else '',
    }


def audit_export_payload(logs: list[dict[str, Any]], export_format: str) -> dict[str, str]:
    if export_format == 'csv':
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ['ID', 'Action', 'Type', 'Resource', 'User', 'Email', 'Tenant', 'Date', 'IP']
        )
        for log in logs:
            writer.writerow(
                [
                    log['id'],
                    log['action'],
                    log['action_type'],
                    log.get('resource_name') or log['resource_type'],
                    log['user_name'],
                    log['user_email'],
                    log.get('tenant_id') or '',
                    log['created_at'],
                    log.get('ip_address') or '',
                ]
            )
        return {'content': buffer.getvalue(), 'mime_type': 'text/csv'}
    return {'content': logs, 'mime_type': 'application/json'}
