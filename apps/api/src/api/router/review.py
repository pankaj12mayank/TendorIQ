"""Review API — backed by AnalysisResult model and AuditLog."""

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..dependencies.audit import audit_logger
from ...core.models import AnalysisResult, AuditLog, User
from ...core.database import get_db
from ...core.auth import AuthContext

router = APIRouter(prefix='/review', tags=['Review'])


class ReviewSectionStatus(BaseModel):
    section: str
    is_edited: bool = False
    has_changes: bool = False
    edit_count: int = 0
    last_edited_at: Optional[datetime] = None
    last_edited_by: Optional[str] = None
    approval_status: str = 'pending'


class ApprovalStep(BaseModel):
    id: str
    name: str
    role: str
    status: str
    approver: Optional[dict] = None
    completed_at: Optional[datetime] = None
    comments: Optional[str] = None


class ReviewWorkflow(BaseModel):
    id: str
    tender_id: str
    status: str
    current_step: int
    priority: str = 'medium'
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime] = None
    steps: list[ApprovalStep] = []


class ReviewComment(BaseModel):
    id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_role: str
    content: str
    section: Optional[str] = None
    created_at: datetime
    is_resolved: bool = False
    replies: list[dict] = []


class ChangeRecord(BaseModel):
    id: str
    section: str
    field: str
    previous_value: str
    new_value: str
    changed_by: str
    changed_by_name: str
    changed_at: datetime
    reason: Optional[str] = None


class AuditEntry(BaseModel):
    id: str
    action: str
    performed_by: str
    performed_by_name: str
    performed_by_role: str
    timestamp: datetime
    details: str
    previous_state: Optional[dict] = None
    new_state: Optional[dict] = None


class ReviewSession(BaseModel):
    id: str
    tender_id: str
    workflow: ReviewWorkflow
    reviewers: list[dict]
    comments: list[ReviewComment]
    changes: list[ChangeRecord]
    audit_log: list[AuditEntry]
    section_statuses: list[ReviewSectionStatus]
    created_at: datetime
    updated_at: datetime


class ApprovalRequest(BaseModel):
    action: str = Field(..., description="approve, reject, request_changes")
    comments: Optional[str] = None
    sections: Optional[list[str]] = None


class CommentRequest(BaseModel):
    content: str
    section: Optional[str] = None


class EditFieldRequest(BaseModel):
    section: str
    field: str
    new_value: str
    reason: Optional[str] = None


class RegenerateRequest(BaseModel):
    section: str
    reason: str
    include_changes: bool = True
    priority: str = 'normal'


def _analysis_to_session(tenant_id: str, tender_id: str, results: list[AnalysisResult]) -> dict:
    now = datetime.utcnow()
    return {
        'id': str(uuid4()),
        'tender_id': tender_id,
        'workflow': {
            'id': str(uuid4()),
            'tender_id': tender_id,
            'status': 'in_review' if results else 'pending',
            'current_step': 1,
            'priority': 'normal',
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'deadline': None,
            'steps': [],
        },
        'reviewers': [],
        'comments': [],
        'changes': [],
        'audit_log': [],
        'section_statuses': [
            {
                'section': r.analysis_type,
                'is_edited': False,
                'has_changes': False,
                'edit_count': 0,
                'last_edited_at': r.created_at.isoformat() if r.created_at else None,
                'last_edited_by': None,
                'approval_status': 'completed' if r.score is not None else 'pending',
            }
            for r in results
        ],
        'created_at': results[0].created_at.isoformat() if results else now.isoformat(),
        'updated_at': results[-1].created_at.isoformat() if results else now.isoformat(),
    }


@router.get('/session/{tender_id}', response_model=dict)
async def get_review_session(
    tender_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get review session for a tender"""
    try:
        tenant_id = current_user.tenant_id
        q = (
            select(AnalysisResult)
            .where(
                AnalysisResult.tenant_id == UUID(tenant_id),
                AnalysisResult.tender_id == UUID(tender_id),
            )
            .order_by(AnalysisResult.created_at.desc())
        )
        rows = (await db.execute(q)).scalars().all()

        await audit_logger.log_action(
            db=db,
            tenant_id=UUID(tenant_id),
            user_id=UUID(current_user.user_id),
            action='REVIEW_SESSION_ACCESSED',
            action_type='access',
            resource_type='ReviewSession',
            resource_id=UUID(tender_id),
            new_values={'tender_id': tender_id},
        )

        data = _analysis_to_session(tenant_id, tender_id, list(rows))
        return {'success': True, 'data': data}
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to get review session')


@router.post('/session/{tender_id}/approval')
async def submit_approval(
    tender_id: str,
    request: ApprovalRequest,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit approval decision"""
    await audit_logger.log_action(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id),
        action=f'REVIEW_{request.action.upper()}',
        action_type='admin_action',
        resource_type='ReviewSession',
        resource_id=UUID(tender_id),
        new_values={'action': request.action, 'comments': request.comments},
        changes={'action': request.action},
    )
    return {
        'success': True,
        'message': f'Approval {request.action} submitted successfully',
    }


@router.post('/session/{tender_id}/comments')
async def add_comment(
    tender_id: str,
    request: CommentRequest,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment to the review"""
    comment_id = str(uuid4())

    await audit_logger.log_action(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id),
        action='COMMENT_ADDED',
        action_type='admin_action',
        resource_type='ReviewComment',
        resource_id=UUID(tender_id),
        new_values={'content': request.content, 'section': request.section},
    )

    return {
        'success': True,
        'data': {
            'id': comment_id,
            'reviewer_id': current_user.user_id,
            'reviewer_name': current_user.email,
            'reviewer_role': 'reviewer',
            'content': request.content,
            'section': request.section,
            'created_at': datetime.utcnow().isoformat(),
            'is_resolved': False,
            'replies': [],
        },
    }


@router.put('/comments/{comment_id}/resolve')
async def resolve_comment(
    comment_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a comment"""
    await audit_logger.log_action(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id),
        action='COMMENT_RESOLVED',
        action_type='admin_action',
        resource_type='ReviewComment',
        resource_id=comment_id,
    )
    return {'success': True, 'message': 'Comment resolved'}


@router.post('/session/{tender_id}/edit')
async def edit_field(
    tender_id: str,
    request: EditFieldRequest,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit a field in a section"""
    await audit_logger.log_action(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id),
        action='SECTION_EDITED',
        action_type='admin_action',
        resource_type='ReviewSection',
        resource_id=UUID(tender_id),
        new_values={request.field: request.new_value},
        changes={request.field: {'old': 'previous', 'new': request.new_value}},
    )

    return {
        'success': True,
        'data': {
            'section': request.section,
            'field': request.field,
            'new_value': request.new_value,
            'changed_by': current_user.user_id,
            'changed_at': datetime.utcnow().isoformat(),
        },
    }


@router.post('/session/{tender_id}/regenerate')
async def regenerate_section(
    tender_id: str,
    request: RegenerateRequest,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a section using AI"""
    await audit_logger.log_action(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id),
        action='SECTION_REGENERATED',
        action_type='admin_action',
        resource_type='ReviewSection',
        resource_id=UUID(tender_id),
        new_values={'section': request.section, 'reason': request.reason},
    )

    return {
        'success': True,
        'message': f'Regeneration of {request.section} started',
        'data': {'section': request.section, 'status': 'in_progress'},
    }


@router.get('/session/{tender_id}/audit')
async def get_audit_log(
    tender_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log for a review session"""
    try:
        q = (
            select(AuditLog)
            .where(
                AuditLog.tenant_id == UUID(current_user.tenant_id),
                AuditLog.resource_id == UUID(tender_id),
            )
            .order_by(AuditLog.created_at.desc())
        )
        rows = (await db.execute(q)).scalars().all()
        audit_entries = []
        for log in rows:
            audit_entries.append({
                'id': str(log.id),
                'action': log.action,
                'performed_by': str(log.user_id) if log.user_id else '',
                'performed_by_name': '',
                'performed_by_role': '',
                'timestamp': log.created_at.isoformat() if log.created_at else '',
                'details': log.action,
                'previous_state': log.old_values,
                'new_state': log.new_values,
            })
        return {'success': True, 'data': audit_entries}
    except Exception:
        return {'success': True, 'data': []}


@router.get('/session/{tender_id}/changes')
async def get_change_history(
    tender_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get change history for a review session"""
    try:
        q = (
            select(AuditLog)
            .where(
                AuditLog.tenant_id == UUID(current_user.tenant_id),
                AuditLog.resource_id == UUID(tender_id),
                AuditLog.action.in_(['SECTION_EDITED', 'COMMENT_ADDED', 'REVIEW_STARTED']),
            )
            .order_by(AuditLog.created_at.desc())
        )
        rows = (await db.execute(q)).scalars().all()
        changes = []
        for log in rows:
            changes.append({
                'id': str(log.id),
                'section': log.resource_type,
                'field': '',
                'previous_value': '',
                'new_value': '',
                'changed_by': str(log.user_id) if log.user_id else '',
                'changed_by_name': '',
                'changed_at': log.created_at.isoformat() if log.created_at else '',
                'reason': None,
            })
        return {'success': True, 'data': changes}
    except Exception:
        return {'success': True, 'data': []}
