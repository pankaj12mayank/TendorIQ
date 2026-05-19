"""Structured Extraction Schemas for Tender Documents"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExtractionStatus(str, Enum):
    PENDING = 'pending'
    EXTRACTING = 'extracting'
    VALIDATED = 'validated'
    FAILED = 'failed'
    PARTIAL = 'partial'


class ConfidenceLevel(float, Enum):
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    UNCERTAIN = 0.3


class TenderSummary(BaseModel):
    title: str = Field(..., description="Tender title")
    reference_number: Optional[str] = Field(None, description="Tender reference/ID number")
    description: str = Field(..., description="Brief description of tender")
    organization: str = Field(..., description="Issuing organization name")
    department: Optional[str] = Field(None, description="Department/section")
    category: Optional[str] = Field(None, description="Tender category")
    type: Optional[str] = Field(None, description="Tender type (open, limited, etc.)")
    summary_confidence: float = Field(default=0.0, ge=0, le=1)


class EligibilityCriteria(BaseModel):
    criteria: list[str] = Field(default_factory=list, description="List of eligibility conditions")
    min_experience_years: Optional[int] = Field(None, description="Minimum experience required")
    required_certifications: list[str] = Field(default_factory=list, description="Required certifications")
    required_registrations: list[str] = Field(default_factory=list, description="Required registrations")
    eligibility_confidence: float = Field(default=0.0, ge=0, le=1)
    exclusions: list[str] = Field(default_factory=list, description="Exclusion criteria")


class TechnicalRequirement(BaseModel):
    specification_id: Optional[str] = Field(None, description="Specification reference ID")
    description: str = Field(..., description="Technical requirement description")
    quantity: Optional[str] = Field(None, description="Quantity/unit")
    standards: list[str] = Field(default_factory=list, description="Required standards/compliance")
    specifications: dict[str, Any] = Field(default_factory=dict, description="Technical specifications")
    technical_confidence: float = Field(default=0.0, ge=0, le=1)


class TechnicalRequirementsCollection(BaseModel):
    requirements: list[TechnicalRequirement] = Field(default_factory=list)
    total_requirements: int = 0
    technical_confidence: float = Field(default=0.0, ge=0, le=1)


class FinancialRequirement(BaseModel):
    item_description: str = Field(..., description="Financial item description")
    estimated_value: Optional[float] = Field(None, description="Estimated value")
    currency: str = Field(default="INR", description="Currency code")
    budget_range: Optional[str] = Field(None, description="Budget range if specified")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    financial_confidence: float = Field(default=0.0, ge=0, le=1)


class FinancialRequirementsCollection(BaseModel):
    items: list[FinancialRequirement] = Field(default_factory=list)
    total_value: Optional[float] = None
    currency: str = "INR"
    has_bid_security: bool = False
    bid_security_amount: Optional[float] = None
    financial_confidence: float = Field(default=0.0, ge=0, le=1)


class Deadline(BaseModel):
    type: str = Field(..., description="Deadline type (submission, pre-bid, etc.)")
    due_date: Optional[date] = Field(None, description="Deadline date")
    due_time: Optional[str] = Field(None, description="Deadline time")
    due_datetime: Optional[datetime] = Field(None, description="Combined datetime")
    description: Optional[str] = Field(None, description="Deadline description")
    is_hard_deadline: bool = Field(default=False, description="Whether deadline is firm")
    days_remaining: Optional[int] = Field(None, description="Days until deadline")
    deadline_confidence: float = Field(default=0.0, ge=0, le=1)


class DeadlinesCollection(BaseModel):
    deadlines: list[Deadline] = Field(default_factory=list)
    submission_deadline: Optional[Deadline] = None
    earliest_deadline: Optional[date] = None
    total_deadlines: int = 0
    deadlines_confidence: float = Field(default=0.0, ge=0, le=1)


class MandatoryDocument(BaseModel):
    document_name: str = Field(..., description="Required document name")
    document_type: Optional[str] = Field(None, description="Document type/format")
    is_mandatory: bool = Field(default=True, description="Whether document is mandatory")
    submission_method: Optional[str] = Field(None, description="How to submit")
    copies_required: Optional[int] = Field(None, description="Number of copies")
    attestation_required: bool = Field(default=False)
    document_confidence: float = Field(default=0.0, ge=0, le=1)


class MandatoryDocumentsCollection(BaseModel):
    documents: list[MandatoryDocument] = Field(default_factory=list)
    total_mandatory: int = 0
    total_optional: int = 0
    documents_confidence: float = Field(default=0.0, ge=0, le=1)


class Clause(BaseModel):
    clause_id: Optional[str] = Field(None, description="Clause reference number")
    title: Optional[str] = Field(None, description="Clause title")
    category: str = Field(..., description="Clause category")
    content: str = Field(..., description="Full clause text")
    is_critical: bool = Field(default=False, description="Whether clause is critical")
    penalty_clause: bool = Field(default=False, description="Whether contains penalty")
    dispute_resolution: Optional[str] = Field(None, description="Dispute resolution mechanism")
    clause_confidence: float = Field(default=0.0, ge=0, le=1)


class ClausesCollection(BaseModel):
    clauses: list[Clause] = Field(default_factory=list)
    total_clauses: int = 0
    critical_count: int = 0
    clauses_confidence: float = Field(default=0.0, ge=0, le=1)


class ContractTerms(BaseModel):
    contract_duration: Optional[str] = Field(None, description="Contract duration")
    renewal_options: Optional[str] = Field(None, description="Renewal/extension options")
    termination_clause: Optional[str] = Field(None, description="Termination conditions")
    warranty_period: Optional[str] = Field(None, description="Warranty period")
    performance_guarantee: Optional[float] = Field(None, description="Performance guarantee amount")
    terms_confidence: float = Field(default=0.0, ge=0, le=1)


class AwardCriteria(BaseModel):
    criteria_name: str = Field(..., description="Award criteria name")
    weightage: Optional[float] = Field(None, description="Weightage percentage", ge=0, le=100)
    description: Optional[str] = Field(None, description="Criteria description")
    is_primary: bool = Field(default=False, description="Primary evaluation criteria")
    award_confidence: float = Field(default=0.0, ge=0, le=1)


class AwardCriteriaCollection(BaseModel):
    criteria: list[AwardCriteria] = Field(default_factory=list)
    total_criteria: int = 0
    evaluation_method: Optional[str] = Field(None, description="Evaluation method")
    award_confidence: float = Field(default=0.0, ge=0, le=1)


class ContactInformation(BaseModel):
    contact_person: Optional[str] = Field(None, description="Contact person name")
    designation: Optional[str] = Field(None, description="Contact person designation")
    department: Optional[str] = Field(None, description="Contact department")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Address")
    website: Optional[str] = Field(None, description="Tender website URL")


class SubmissionGuidelines(BaseModel):
    method: Optional[str] = Field(None, description="Submission method")
    format_required: list[str] = Field(default_factory=list, description="Required formats")
    language: str = Field(default="English", description="Submission language")
    number_of_copies: Optional[int] = Field(None, description="Number of copies")
    size_limits: Optional[str] = Field(None, description="File size limits")
    guidelines_confidence: float = Field(default=0.0, ge=0, le=1)


class CompleteExtractionResult(BaseModel):
    document_id: Optional[UUID] = None
    extraction_id: str = Field(default_factory=lambda: str(UUID()))
    status: ExtractionStatus = ExtractionStatus.PENDING

    tender_summary: Optional[TenderSummary] = None
    eligibility_criteria: Optional[EligibilityCriteria] = None
    technical_requirements: Optional[TechnicalRequirementsCollection] = None
    financial_requirements: Optional[FinancialRequirementsCollection] = None
    deadlines: Optional[DeadlinesCollection] = None
    mandatory_documents: Optional[MandatoryDocumentsCollection] = None
    clauses: Optional[ClausesCollection] = None
    contract_terms: Optional[ContractTerms] = None
    award_criteria: Optional[AwardCriteriaCollection] = None
    contact_information: Optional[ContactInformation] = None
    submission_guidelines: Optional[SubmissionGuidelines] = None

    overall_confidence: float = Field(default=0.0, ge=0, le=1)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('overall_confidence')
    @classmethod
    def calculate_overall_confidence(cls, v, info):
        return v

    def is_complete(self) -> bool:
        required_fields = [
            self.tender_summary,
            self.eligibility_criteria,
            self.deadlines,
        ]
        return all(f is not None for f in required_fields)


class ExtractionRequest(BaseModel):
    document_id: UUID
    tenant_id: Optional[UUID] = None
    extraction_type: str = Field(default="full", description="full, summary, quick")
    fields_to_extract: Optional[list[str]] = Field(None, description="Specific fields")
    validation_strict: bool = Field(default=False, description="Strict validation")
    retry_on_failure: bool = Field(default=True, description="Auto retry failed extractions")


class ExtractionResponse(BaseModel):
    extraction_id: str
    status: ExtractionStatus
    result: Optional[CompleteExtractionResult] = None
    confidence: float = 0.0
    processing_time_ms: int = 0
    retry_count: int = 0
    errors: list[str] = Field(default_factory=list)