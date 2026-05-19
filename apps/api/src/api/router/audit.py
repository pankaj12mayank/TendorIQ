"""Enterprise Audit Logging API"""

import logging
import enum
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field

from ....core.models import AuditLog
from ....core.database import get_db
from ....dependencies.auth import get_current_user
from ....core.auth import AuthContext
from ....dependencies.audit import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/audit', tags=['Audit'])


class AuditActionType(str, enum):
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


MOCK_LOGS = [
    {
        'id': 'a1',
        'action': 'FILE_UPLOADED',
        'action_type': 'upload',
        'resource_type': 'document',
        'resource_id': 'doc-123',
        'resource_name': 'tender_document.pdf',
        'user_id': 'user-1',
        'user_name': 'John Doe',
        'user_email': 'john@example.com',
        'user_role': 'analyst',
        'tenant_id': 'tenant-1',
        'changes': {'status': 'uploaded'},
        'old_values': {},
        'new_values': {'status': 'uploaded', 'size': 2048576},
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0',
        'request_id': 'req-123',
        'created_at': '2026-05-19T10:30:00Z'
    },
    {
        'id': 'a2',
        'action': 'TENDER_EXPORTED',
        'action_type': 'export',
        'resource_type': 'tender',
        'resource_id': 'tend-456',
        'resource_name': 'IT Infrastructure Tender',
        'user_id': 'user-2',
        'user_name': 'Jane Smith',
        'user_email': 'jane@example.com',
        'user_role': 'manager',
        'tenant_id': 'tenant-1',
        'changes': {'format': 'pdf', 'pages': 45},
        'old_values': {},
        'new_values': {'export_format': 'pdf'},
        'ip_address': '192.168.1.101',
        'user_agent': 'Mozilla/5.0',
        'request_id': 'req-124',
        'created_at': '2026-05-19T11:00:00Z'
    },
    {
        'id': 'a3',
        'action': 'AI_ANALYSIS_COMPLETED',
        'action_type': 'ai_generation',
        'resource_type': 'analysis',
        'resource_id': 'analysis-789',
        'resource_name': 'Tender Analysis',
        'user_id': 'user-1',
        'user_name': 'John Doe',
        'user_email': 'john@example.com',
        'user_role': 'analyst',
        'tenant_id': 'tenant-1',
        'changes': {'confidence': 85, 'sections': 7},
        'old_values': {'status': 'processing'},
        'new_values': {'status': 'completed'},
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0',
        'request_id': 'req-125',
        'created_at': '2026-05-19T11:30:00Z'
    },
    {
        'id': 'a4',
        'action': 'USER_ROLE_CHANGED',
        'action_type': 'admin_action',
        'resource_type': 'user',
        'resource_id': 'user-3',
        'resource_name': 'Bob Wilson',
        'user_id': 'user-2',
        'user_name': 'Jane Smith',
        'user_email': 'jane@example.com',
        'user_role': 'manager',
        'tenant_id': 'tenant-1',
        'changes': {'role': 'admin'},
        'old_values': {'role': 'viewer'},
        'new_values': {'role': 'admin'},
        'ip_address': '192.168.1.101',
        'user_agent': 'Mozilla/5.0',
        'request_id': 'req-126',
        'created_at': '2026-05-19T12:00:00Z'
    },
    {
        'id': 'a5',
        'action': 'SUBSCRIPTION_UPGRADED',
        'action_type': 'billing',
        'resource_type': 'subscription',
        'resource_id': 'sub-001',
        'resource_name': 'Pro Plan',
        'user_id': 'user-2',
        'user_name': 'Jane Smith',
        'user_email': 'jane@example.com',
        'user_role': 'manager',
        'tenant_id': 'tenant-1',
        'changes': {'plan': 'pro', 'billing': 'monthly'},
        'old_values': {'plan': 'free'},
        'new_values': {'plan': 'pro'},
        'ip_address': '192.168.1.101',
        'user_agent': 'Mozilla/5.0',
        'request_id': 'req-127',
        'created_at': '2026-05-19T12:30:00Z'
    },
    {
        'id': 'a6',
        'action': 'DOCUMENT_DELETED',
        'action_type': 'delete',
        'resource_type': 'document',
        'resource_id': 'doc-999',
        'resource_name': 'old_tender.pdf',
        'user_id': 'user-1',
        'user_name': 'John Doe',
        'user_email': 'john@example.com',
        'user_role': 'analyst',
        'tenant_id': 'tenant-1',
        'changes': {'status': 'deleted'},
        'old_values': {'status': 'active'},
        'new_values': {'status': 'deleted'},
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0',
        'request_id': 'req-128',
        'created_at': '2026-05-19T13:00:00Z'
    }
]


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
    
    logs = MOCK_LOGS
    
    if action:
        logs = [l for l in logs if l['action'] == action]
    if action_type:
        logs = [l for l in logs if l['action_type'] == action_type]
    if resource_type:
        logs = [l for l in logs if l['resource_type'] == resource_type]
    if resource_id:
        logs = [l for l in logs if l['resource_id'] == resource_id]
    if user_id:
        logs = [l for l in logs if l['user_id'] == user_id]
    if search:
        search_lower = search.lower()
        logs = [l for l in logs if search_lower in l['user_name'].lower() or 
                search_lower in l['resource_name'].lower() or 
                search_lower in l['action'].lower()]
    
    return logs[offset:offset+limit]


@router.get('/logs/{log_id}', response_model=AuditEntry)
async def get_audit_log(
    log_id: str,
    current_user: AuthContext = Depends(get_current_user),
):
    """Get a specific audit log entry"""
    
    for log in MOCK_LOGS:
        if log['id'] == log_id:
            return log
    
    raise HTTPException(status_code=404, detail='Audit log not found')


@router.get('/stats', response_model=AuditStats)
async def get_audit_stats(
    days: int = Query(30, le=365),
    current_user: AuthContext = Depends(get_current_user),
):
    """Get audit statistics"""
    
    entries_by_action = {}
    entries_by_type = {}
    entries_by_user = {}
    
    for log in MOCK_LOGS:
        action = log['action']
        entries_by_action[action] = entries_by_action.get(action, 0) + 1
        
        action_type = log['action_type']
        entries_by_type[action_type] = entries_by_type.get(action_type, 0) + 1
        
        user = log['user_name']
        entries_by_user[user] = entries_by_user.get(user, 0) + 1
    
    daily_trend = [
        {'date': '2026-05-19', 'count': len(MOCK_LOGS)},
        {'date': '2026-05-18', 'count': 12},
        {'date': '2026-05-17', 'count': 8},
    ]
    
    return AuditStats(
        total_entries=len(MOCK_LOGS),
        entries_by_action=entries_by_action,
        entries_by_type=entries_by_type,
        entries_by_user=entries_by_user,
        daily_trend=daily_trend
    )


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
):
    """Export audit logs in specified format"""
    
    logs = MOCK_LOGS
    
    if request.action_types:
        logs = [l for l in logs if l['action_type'] in request.action_types]
    if request.start_date:
        logs = [l for l in logs if l['created_at'] >= request.start_date.isoformat()]
    if request.end_date:
        logs = [l for l in logs if l['created_at'] <= request.end_date.isoformat()]
    
    if request.format == 'csv':
        csv_content = 'ID,Action,Type,Resource,User,Date\n'
        for log in logs:
            csv_content += f"{log['id']},{log['action']},{log['action_type']},{log['resource_name']},{log['user_name']},{log['created_at']}\n"
        return {'content': csv_content, 'mime_type': 'text/csv'}
    
    return {'content': logs, 'mime_type': 'application/json'}


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
    
    log_entry = {
        'id': f'audit-{datetime.utcnow().timestamp()}',
        'action': action,
        'action_type': action_type,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'resource_name': resource_name,
        'user_id': current_user.user_id,
        'user_name': current_user.email,
        'user_email': current_user.email,
        'user_role': current_user.role,
        'tenant_id': str(current_user.tenant_id) if hasattr(current_user, 'tenant_id') else 'unknown',
        'changes': changes,
        'old_values': old_values,
        'new_values': new_values,
        'created_at': datetime.utcnow().isoformat()
    }
    
    MOCK_LOGS.insert(0, log_entry)
    
    return {'success': True, 'log_id': log_entry['id']}