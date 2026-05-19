from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..dependencies.audit import audit_logger
from ...core.models import User
from ...core.database import get_db

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


MOCK_REVIEW_SESSION = {
    'id': 'RS-2026-001',
    'tender_id': 'IIT-2026-001',
    'workflow': {
        'id': 'WF-2026-001',
        'tender_id': 'IIT-2026-001',
        'status': 'in_review',
        'current_step': 1,
        'priority': 'high',
        'created_at': '2026-05-18T08:00:00Z',
        'updated_at': '2026-05-18T14:30:00Z',
        'deadline': '2026-05-25T17:00:00Z',
        'steps': [
            {'id': 'step-1', 'name': 'Initial Review', 'role': 'analyst', 'status': 'completed', 'approver': {'id': '1', 'name': 'Sarah Johnson'}, 'completed_at': '2026-05-18T10:00:00Z'},
            {'id': 'step-2', 'name': 'Manager Approval', 'role': 'manager', 'status': 'in_progress', 'approver': {'id': '2', 'name': 'Mike Chen'}},
            {'id': 'step-3', 'name': 'Director Sign-off', 'role': 'director', 'status': 'pending'},
        ]
    },
    'reviewers': [
        {'id': '1', 'name': 'Sarah Johnson', 'email': 'sarah@company.com', 'role': 'analyst'},
        {'id': '2', 'name': 'Mike Chen', 'email': 'mike@company.com', 'role': 'manager'},
    ],
    'comments': [
        {'id': 'c1', 'reviewer_id': '1', 'reviewer_name': 'Sarah Johnson', 'reviewer_role': 'Analyst', 'content': 'Financial section looks good', 'section': 'financial', 'created_at': '2026-05-18T09:00:00Z', 'is_resolved': False, 'replies': []}
    ],
    'changes': [],
    'audit_log': [
        {'id': 'a1', 'action': 'REVIEW_STARTED', 'performed_by': '1', 'performed_by_name': 'Sarah Johnson', 'performed_by_role': 'Analyst', 'timestamp': '2026-05-18T08:00:00Z', 'details': 'Review initiated'}
    ],
    'section_statuses': [
        {'section': 'summary', 'is_edited': False, 'has_changes': False, 'edit_count': 0, 'approval_status': 'approved'},
        {'section': 'eligibility', 'is_edited': False, 'has_changes': False, 'edit_count': 0, 'approval_status': 'pending'},
        {'section': 'technical', 'is_edited': False, 'has_changes': False, 'edit_count': 0, 'approval_status': 'pending'},
        {'section': 'financial', 'is_edited': False, 'has_changes': False, 'edit_count': 0, 'approval_status': 'pending'},
        {'section': 'risks', 'is_edited': False, 'has_changes': False, 'edit_count': 0, 'approval_status': 'pending'},
        {'section': 'deadlines', 'is_edited': False, 'has_changes': False, 'edit_count': 0, 'approval_status': 'pending'},
        {'section': 'mandatory_docs', 'is_edited': False, 'has_changes': False, 'edit_count': 0, 'approval_status': 'pending'},
    ],
    'created_at': '2026-05-18T08:00:00Z',
    'updated_at': '2026-05-18T14:30:00Z',
}


@router.get('/session/{tender_id}', response_model=dict)
async def get_review_session(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get review session for a tender"""
    await audit_logger.log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action='REVIEW_SESSION_ACCESSED',
        resource_type='ReviewSession',
        details=f'Accessed review session for tender {tender_id}',
    )
    return {'success': True, 'data': MOCK_REVIEW_SESSION}


@router.post('/session/{tender_id}/approval')
async def submit_approval(
    tender_id: str,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit approval decision"""
    await audit_logger.log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=f'REVIEW_{request.action.upper()}',
        resource_type='ReviewSession',
        resource_id=tender_id,
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment to the review"""
    comment_id = f'comment-{datetime.utcnow().timestamp()}'
    
    await audit_logger.log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action='COMMENT_ADDED',
        resource_type='ReviewComment',
        new_values={'content': request.content, 'section': request.section},
    )
    
    return {
        'success': True,
        'data': {
            'id': comment_id,
            'reviewer_id': str(current_user.id),
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a comment"""
    await audit_logger.log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action='COMMENT_RESOLVED',
        resource_type='ReviewComment',
        resource_id=comment_id,
    )
    return {'success': True, 'message': 'Comment resolved'}


@router.post('/session/{tender_id}/edit')
async def edit_field(
    tender_id: str,
    request: EditFieldRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit a field in a section"""
    await audit_logger.log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action='SECTION_EDITED',
        resource_type='ReviewSection',
        resource_id=tender_id,
        new_values={request.field: request.new_value},
        changes={request.field: {'old': 'previous', 'new': request.new_value}},
    )
    
    return {
        'success': True,
        'data': {
            'section': request.section,
            'field': request.field,
            'new_value': request.new_value,
            'changed_by': str(current_user.id),
            'changed_at': datetime.utcnow().isoformat(),
        },
    }


@router.post('/session/{tender_id}/regenerate')
async def regenerate_section(
    tender_id: str,
    request: RegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a section using AI"""
    await audit_logger.log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action='SECTION_REGENERATED',
        resource_type='ReviewSection',
        resource_id=tender_id,
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log for a review session"""
    return {
        'success': True,
        'data': MOCK_REVIEW_SESSION['audit_log'],
    }


@router.get('/session/{tender_id}/changes')
async def get_change_history(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get change history for a review session"""
    return {
        'success': True,
        'data': MOCK_REVIEW_SESSION['changes'],
    }