"""Enterprise Audit Logging API"""

import enum
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from ...core.audit_limits import clamp_export_limit
from ...core.audit_present import audit_export_payload, audit_log_to_dict, load_users_by_id
from ...core.models import AuditLog
from ...core.database import get_db
from ..dependencies.rbac_deps import RequireAnalyticsView
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


class AuditExportRequest(BaseModel):
    format: str = Field(default='json', pattern='^(json|csv)$')
    action_types: Optional[list[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = Field(default=None, ge=1, le=10000)


class AuditStats(BaseModel):
    total_entries: int
    entries_by_action: dict
    entries_by_type: dict
    entries_by_user: dict
    daily_trend: list


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
        conditions.append(func.lower(AuditLog.action).like(f'%{search_lower}%'))
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    return conditions


async def _entries_for_tenant(db, tenant_id: UUID, conditions: list, limit: int, offset: int) -> list[dict]:
    q = (
        select(AuditLog)
        .where(*conditions)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    user_ids = {r.user_id for r in rows if r.user_id}
    users = await load_users_by_id(db, user_ids)
    return [audit_log_to_dict(r, users.get(r.user_id)) for r in rows]


@router.get('/logs', response_model=list[AuditEntry])
async def get_audit_logs(
    current_user: RequireAnalyticsView,
    db=Depends(get_db),
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
):
    """Get tenant-scoped audit logs with filtering."""
    tenant_id = UUID(current_user.tenant_id)
    conditions = _build_filters(
        tenant_id,
        action,
        action_type,
        resource_type,
        resource_id,
        user_id,
        search,
        start_date,
        end_date,
    )
    return await _entries_for_tenant(db, tenant_id, conditions, limit, offset)


@router.get('/logs/{log_id}', response_model=AuditEntry)
async def get_audit_log(
    log_id: str,
    current_user: RequireAnalyticsView,
    db=Depends(get_db),
):
    """Get a specific audit log entry."""
    tenant_id = UUID(current_user.tenant_id)
    try:
        log_uuid = UUID(log_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail='Audit log not found') from exc

    row = (
        await db.execute(
            select(AuditLog).where(AuditLog.id == log_uuid, AuditLog.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail='Audit log not found')

    users = await load_users_by_id(db, {row.user_id} if row.user_id else set())
    return audit_log_to_dict(row, users.get(row.user_id))


@router.get('/stats', response_model=AuditStats)
async def get_audit_stats(
    current_user: RequireAnalyticsView,
    db=Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get audit statistics for the current tenant."""
    tenant_id = UUID(current_user.tenant_id)
    total = await db.scalar(select(func.count(AuditLog.id)).where(AuditLog.tenant_id == tenant_id)) or 0

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

    since = datetime.now(timezone.utc) - timedelta(days=days)
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


@router.get('/actions')
async def get_audit_actions(
    _user: RequireAnalyticsView,
):
    """Get available audit action types."""
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
    body: AuditExportRequest,
    http_request: Request,
    current_user: RequireAnalyticsView,
    db=Depends(get_db),
):
    """Export tenant audit logs."""
    tenant_id = UUID(current_user.tenant_id)
    conditions = [AuditLog.tenant_id == tenant_id]
    if body.action_types:
        conditions.append(AuditLog.action_type.in_(body.action_types))
    if body.start_date:
        conditions.append(AuditLog.created_at >= body.start_date)
    if body.end_date:
        conditions.append(AuditLog.created_at <= body.end_date)

    export_limit = clamp_export_limit(body.limit)
    rows = (
        await db.execute(
            select(AuditLog)
            .where(*conditions)
            .order_by(AuditLog.created_at.desc())
            .limit(export_limit)
        )
    ).scalars().all()
    user_ids = {r.user_id for r in rows if r.user_id}
    users = await load_users_by_id(db, user_ids)
    logs = [audit_log_to_dict(r, users.get(r.user_id)) for r in rows]

    if current_user.user_id:
        await audit_logger.log_action(
            db,
            tenant_id,
            UUID(current_user.user_id),
            action='export',
            action_type='export',
            resource_type='audit_log',
            new_values={'format': body.format, 'row_count': len(logs), 'limit': export_limit},
            request=http_request,
        )

    return audit_export_payload(logs, body.format)


@router.post('/track')
async def track_audit_event(
    request: Request,
    current_user: RequireAnalyticsView,
    action: str,
    action_type: str,
    resource_type: str,
    db=Depends(get_db),
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    changes: dict = {},
    old_values: dict = {},
    new_values: dict = {},
):
    """Track a custom audit event (tenant-scoped)."""
    tenant_id = UUID(current_user.tenant_id)
    user_id = UUID(current_user.user_id) if current_user.user_id else None
    if not user_id:
        raise HTTPException(status_code=400, detail='User context required')

    log = await audit_logger.log_action(
        db,
        tenant_id,
        user_id,
        action=action,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=UUID(resource_id) if resource_id else None,
        resource_name=resource_name,
        changes=changes or {},
        old_values=old_values or {},
        new_values=new_values or {},
        request=request,
    )
    return {'success': True, 'log_id': str(log.id)}
