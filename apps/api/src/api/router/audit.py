"""Enterprise Audit Logging API"""

import logging
import enum
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...core.models import AuditLog
from ...core.database import get_db
from ..dependencies.auth import get_current_user
from ...core.auth import AuthContext
from ..dependencies.audit import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/audit', tags=['Audit'])


class AuditActionType(str, enum.Enum):
    UPLOAD = 'upload'
    DELETE = 'delete'
    EXPORT = 'export'
    ADMIN_ACTION = 'admin_action'
    AI_GENERATION = 'ai_generation'
    BILLING = 'billing'
    USER = 'user'
    DOCUMENT = 'document'
    TENDER = 'tender'
    BID = 'bid'
    SETTINGS = 'settings'
    AUTH = 'auth'


class AuditEntry(BaseModel):
    id: str
    action: str
    action_type: str
    resource_type: str
    resource_id: Optional[str]
    resource_name: Optional[str]
    user_id: str
    user_name: str
    user_email: str
    user_role: str
    tenant_id: str
    changes: dict
    old_values: dict
    new_values: dict
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    created_at: str


class AuditQueryParams(BaseModel):
    action: Optional[str] = None
    action_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None


class AuditExportRequest(BaseModel):
    format: str = Field(default='json', pattern='^(json|csv)$')
    action_types: Optional[list[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AuditStats(BaseModel):
    total_entries: int
    entries_by_action: dict
    entries_by_type: dict
    entries_by_user: dict
    daily_trend: list


def _log_to_entry(log: AuditLog) -> dict:
    return {
        'id': str(log.id),
        'action': log.action,
        'action_type': log.action_type,
        'resource_type': log.resource_type,
        'resource_id': str(log.resource_id) if log.resource_id else None,
        'resource_name': log.resource_name,
        'user_id': str(log.user_id) if log.user_id else '',
        'user_name': '',
        'user_email': '',
        'user_role': '',
        'tenant_id': str(log.tenant_id),
        'changes': log.changes or {},
        'old_values': log.old_values or {},
        'new_values': log.new_values or {},
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'request_id': log.request_id,
        'created_at': log.created_at.isoformat() if log.created_at else '',
    }


def _build_filters(
    tenant_id: UUID,
    action: Optional[str] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    conditions = [AuditLog.tenant_id == tenant_id]
    if action:
        conditions.append(AuditLog.action == action)
    if action_type:
        conditions.append(AuditLog.action_type == action_type)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)
    if user_id:
        conditions.append(AuditLog.user_id == UUID(user_id))
    if search:
        search_lower = search.lower()
        conditions.append(
            func.lower(AuditLog.action).like(f'%{search_lower}%')
        )
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    return conditions


@router.get('/logs', response_model=list[AuditEntry])
async def get_audit_logs(
    action: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: AuthContext = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get audit logs with filtering and search"""
    try:
        tenant_id = UUID(current_user.tenant_id) if current_user.tenant_id else None
        if not tenant_id:
            return []

        conditions = _build_filters(
            tenant_id, action, action_type, resource_type,
            resource_id, user_id, search, start_date, end_date,
        )
        q = (
            select(AuditLog)
            .where(*conditions)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        return [_log_to_entry(r) for r in rows]
    except Exception:
        logger.exception('Failed to fetch audit logs')
        return []


@router.get('/logs/{log_id}', response_model=AuditEntry)
async def get_audit_log(
    log_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get a specific audit log entry"""
    try:
        tenant_id = UUID(current_user.tenant_id) if current_user.tenant_id else None
        q = select(AuditLog).where(
            AuditLog.id == log_id,
            AuditLog.tenant_id == tenant_id,
        )
        row = (await db.execute(q)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail='Audit log not found')
        return _log_to_entry(row)
    except HTTPException:
        raise
    except Exception:
        logger.exception('Failed to fetch audit log')
        raise HTTPException(status_code=404, detail='Audit log not found')


@router.get('/stats', response_model=AuditStats)
async def get_audit_stats(
    days: int = Query(30, le=365),
    current_user: AuthContext = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get audit statistics"""
    try:
        tenant_id = UUID(current_user.tenant_id) if current_user.tenant_id else None
        if not tenant_id:
            return AuditStats(total_entries=0, entries_by_action={}, entries_by_type={}, entries_by_user={}, daily_trend=[])

        total_q = select(func.count(AuditLog.id)).where(AuditLog.tenant_id == tenant_id)
        total = await db.scalar(total_q) or 0

        action_rows = await db.execute(
            select(AuditLog.action, func.count(AuditLog.id).label('cnt'))
            .where(AuditLog.tenant_id == tenant_id)
            .group_by(AuditLog.action)
        )
        entries_by_action = {row[0]: row[1] for row in action_rows.all()}

        type_rows = await db.execute(
            select(AuditLog.action_type, func.count(AuditLog.id).label('cnt'))
            .where(AuditLog.tenant_id == tenant_id)
            .group_by(AuditLog.action_type)
        )
        entries_by_type = {row[0]: row[1] for row in type_rows.all()}

        user_rows = await db.execute(
            select(AuditLog.user_id, func.count(AuditLog.id).label('cnt'))
            .where(AuditLog.tenant_id == tenant_id)
            .group_by(AuditLog.user_id)
        )
        entries_by_user = {str(row[0]): row[1] for row in user_rows.all() if row[0]}

        since = datetime.utcnow() - timedelta(days=days)
        trend_rows = await db.execute(
            select(
                func.date(AuditLog.created_at).label('day'),
                func.count(AuditLog.id).label('cnt'),
            )
            .where(AuditLog.tenant_id == tenant_id, AuditLog.created_at >= since)
            .group_by(func.date(AuditLog.created_at))
            .order_by(func.date(AuditLog.created_at))
        )
        daily_trend = [{'date': str(row[0]), 'count': row[1]} for row in trend_rows.all()]

        return AuditStats(
            total_entries=total,
            entries_by_action=entries_by_action,
            entries_by_type=entries_by_type,
            entries_by_user=entries_by_user,
            daily_trend=daily_trend,
        )
    except Exception:
        logger.exception('Failed to fetch audit stats')
        return AuditStats(total_entries=0, entries_by_action={}, entries_by_type={}, entries_by_user={}, daily_trend=[])


@router.get('/actions')
async def get_audit_actions(current_user: AuthContext = Depends(get_current_user)):
    """Get available audit action types"""
    return {
        'actions': [
            {'value': 'upload', 'label': 'Uploads', 'icon': 'Upload'},
            {'value': 'delete', 'label': 'Deletions', 'icon': 'Trash'},
            {'value': 'export', 'label': 'Exports', 'icon': 'Download'},
            {'value': 'admin_action', 'label': 'Admin Actions', 'icon': 'Shield'},
            {'value': 'ai_generation', 'label': 'AI Generations', 'icon': 'Cpu'},
            {'value': 'billing', 'label': 'Billing Actions', 'icon': 'CreditCard'},
            {'value': 'user', 'label': 'User Actions', 'icon': 'User'},
            {'value': 'document', 'label': 'Documents', 'icon': 'File'},
            {'value': 'tender', 'label': 'Tenders', 'icon': 'Briefcase'},
            {'value': 'bid', 'label': 'Bids', 'icon': 'TrendingUp'},
            {'value': 'settings', 'label': 'Settings', 'icon': 'Settings'},
            {'value': 'auth', 'label': 'Authentication', 'icon': 'Lock'},
        ]
    }


@router.post('/export')
async def export_audit_logs(
    request: AuditExportRequest,
    current_user: AuthContext = Depends(get_current_user),
    db = Depends(get_db),
):
    """Export audit logs in specified format"""
    try:
        tenant_id = UUID(current_user.tenant_id) if current_user.tenant_id else None
        conditions = [AuditLog.tenant_id == tenant_id]

        if request.action_types:
            conditions.append(AuditLog.action_type.in_(request.action_types))
        if request.start_date:
            conditions.append(AuditLog.created_at >= request.start_date)
        if request.end_date:
            conditions.append(AuditLog.created_at <= request.end_date)

        q = select(AuditLog).where(*conditions).order_by(AuditLog.created_at.desc())
        rows = (await db.execute(q)).scalars().all()
        logs = [_log_to_entry(r) for r in rows]

        if request.format == 'csv':
            csv_content = 'ID,Action,Type,Resource,User,Date\n'
            for log in logs:
                csv_content += f"{log['id']},{log['action']},{log['action_type']},{log['resource_name']},{log['user_name']},{log['created_at']}\n"
            return {'content': csv_content, 'mime_type': 'text/csv'}

        return {'content': logs, 'mime_type': 'application/json'}
    except Exception:
        logger.exception('Failed to export audit logs')
        return {'content': [], 'mime_type': 'application/json'}


@router.post('/track')
async def track_audit_event(
    action: str,
    action_type: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    changes: dict = {},
    old_values: dict = {},
    new_values: dict = {},
    current_user: AuthContext = Depends(get_current_user),
    db = Depends(get_db),
):
    """Track a custom audit event"""
    try:
        tenant_id = UUID(current_user.tenant_id) if current_user.tenant_id else None
        log = AuditLog(
            tenant_id=tenant_id,
            user_id=UUID(current_user.user_id) if current_user.user_id else None,
            action=action,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=UUID(resource_id) if resource_id else None,
            resource_name=resource_name,
            changes=changes or {},
            old_values=old_values or {},
            new_values=new_values or {},
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return {'success': True, 'log_id': str(log.id)}
    except Exception:
        await db.rollback()
        logger.exception('Failed to track audit event')
        return {'success': False, 'log_id': None}
