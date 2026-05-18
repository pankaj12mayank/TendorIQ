"""Compliance Checklist Schemas"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, Any, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChecklistStatus(str, Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    SUBMITTED = 'submitted'
    REJECTED = 'rejected'


class DocumentStatus(str, Enum):
    NOT_STARTED = 'not_started'
    COLLECTING = 'collecting'
    PREPARING = 'preparing'
    READY = 'ready'
    SUBMITTED = 'submitted'
    REJECTED = 'rejected'
    EXPIRED = 'expired'


class DocumentType(str, Enum):
    CERTIFICATE = 'certificate'
    REGISTRATION = 'registration'
    LICENSE = 'license'
    DECLARATION = 'declaration'
    FINANCIAL_DOCUMENT = 'financial_document'
    TECHNICAL_DOCUMENT = 'technical_document'
    EXPERIENCE_PROOF = 'experience_proof'
    IDENTITY_PROOF = 'identity_proof'
    OTHER = 'other'


class ChecklistItem(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Document/item name")
    description: Optional[str] = Field(None, description="Detailed description")
    document_type: DocumentType = DocumentType.OTHER

    is_mandatory: bool = Field(default=True, description="Whether item is mandatory")
    is_submitted: bool = Field(default=False, description="Whether item is submitted")
    is_waivable: bool = Field(default=False, description="Whether can be waived")

    status: DocumentStatus = DocumentStatus.NOT_STARTED
    progress_percent: float = Field(default=0.0, ge=0, le=100)

    due_date: Optional[date] = Field(None, description="Submission deadline")
    days_remaining: Optional[int] = Field(None, description="Days until due")

    attachments: list[str] = Field(default_factory=list, description="File paths/IDs")
    attachment_count: int = 0

    notes: Optional[str] = Field(None, description="Additional notes")
    rejection_reason: Optional[str] = Field(None, description="If rejected, reason")
    waiver_status: Optional[str] = Field(None, description="Waiver request status")

    responsible_person: Optional[str] = Field(None, description="Who is responsible")
    estimated_time_minutes: Optional[int] = Field(None, description="Time to prepare")

    order: int = 0
    depends_on: list[str] = Field(default_factory=list, description="Item IDs this depends on")
    category: Optional[str] = Field(None, description="Item category")


class ChecklistSection(BaseModel):
    section_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Section name")
    description: Optional[str] = Field(None)
    order: int = 0

    items: list[ChecklistItem] = Field(default_factory=list)
    mandatory_count: int = 0
    optional_count: int = 0
    completed_count: int = 0

    progress_percent: float = Field(default=0.0, ge=0, le=100)
    is_expanded: bool = True


class SubmissionStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Step name")
    description: Optional[str] = Field(None)
    order: int = 0

    instructions: list[str] = Field(default_factory=list, description="Step instructions")
    required_documents: list[str] = Field(default_factory=list, description="Required doc IDs")
    required_items: list[str] = Field(default_factory=list, description="Required checklist item IDs")

    is_completed: bool = Field(default=False)
    completed_at: Optional[datetime] = Field(None)
    completed_by: Optional[str] = Field(None)

    estimated_duration_minutes: Optional[int] = None
    depends_on_steps: list[str] = Field(default_factory=list)


class ComplianceScore(BaseModel):
    total_items: int = 0
    mandatory_items: int = 0
    completed_items: int = 0
    pending_items: int = 0
    missing_items: int = 0

    mandatory_completed: int = 0
    mandatory_pending: int = 0

    overall_score: float = Field(default=0.0, ge=0, le=100)
    mandatory_score: float = Field(default=0.0, ge=0, le=100)
    optional_score: float = Field(default=0.0, ge=0, le=100)

    compliance_percentage: float = Field(default=0.0, ge=0, le=100)
    readiness_percentage: float = Field(default=0.0, ge=0, le=100)

    risk_level: str = Field(default='low', description="low, medium, high, critical")
    submission_probability: float = Field(default=0.0, ge=0, le=100, description="Chance of successful submission")


class MissingItemAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    item_name: str
    item_id: Optional[str] = None

    category: str
    priority: str = Field(default='high', description="high, medium, low")
    severity: str = Field(default='critical', description="critical, high, medium, low")

    deadline: Optional[date] = None
    days_remaining: Optional[int] = None

    impact: str = Field(default='Cannot submit tender without this item')
    action_required: str
    suggested_deadline: Optional[str] = Field(None, description="Suggested completion date")

    is_resolved: bool = False
    resolution_notes: Optional[str] = None


class ChecklistExportFormat(str, Enum):
    PDF = 'pdf'
    EXCEL = 'excel'
    CSV = 'csv'
    JSON = 'json'
    HTML = 'html'
    MARKDOWN = 'markdown'


class ChecklistExportConfig(BaseModel):
    format: ChecklistExportFormat = ChecklistExportFormat.PDF
    include_completed: bool = True
    include_pending: bool = True
    include_optional: bool = False
    include_instructions: bool = True
    include_due_dates: bool = True
    include_notes: bool = True
    group_by_category: bool = True
    sort_by_deadline: bool = True

    include_progress: bool = True
    include_signatures: bool = False
    page_size: str = Field(default='A4')

    title: Optional[str] = None
    organization_name: Optional[str] = None


class CompleteChecklist(BaseModel):
    checklist_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: Optional[UUID] = None
    tender_id: Optional[UUID] = None

    name: str = Field(..., description="Checklist name")
    description: Optional[str] = None

    status: ChecklistStatus = ChecklistStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None

    sections: list[ChecklistSection] = Field(default_factory=list)
    submission_steps: list[SubmissionStep] = Field(default_factory=list)

    score: ComplianceScore = Field(default_factory=ComplianceScore)
    missing_items: list[MissingItemAlert] = Field(default_factory=list)

    overall_progress: float = Field(default=0.0, ge=0, le=100)
    completion_percentage: float = Field(default=0.0, ge=0, le=100)

    total_items: int = 0
    mandatory_items: int = 0
    optional_items: int = 0
    completed_items: int = 0

    upcoming_deadlines: list[dict] = Field(default_factory=list)
    overdue_items: list[dict] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)


class ChecklistGenerationRequest(BaseModel):
    document_id: UUID
    document_text: str = Field(..., min_length=100)
    tender_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    include_optional_items: bool = True
    group_by_category: bool = True
    sort_by_deadline: bool = True


class ChecklistGenerationResponse(BaseModel):
    checklist_id: str
    status: ChecklistStatus
    name: str
    total_items: int
    mandatory_items: int
    optional_items: int
    estimated_time_hours: float
    generation_time_ms: int
    confidence: float
    warnings: list[str]


class ChecklistUpdateRequest(BaseModel):
    item_id: str
    status: Optional[DocumentStatus] = None
    is_submitted: Optional[bool] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ChecklistExportRequest(BaseModel):
    checklist_id: str
    config: ChecklistExportConfig = Field(default_factory=ChecklistExportConfig)