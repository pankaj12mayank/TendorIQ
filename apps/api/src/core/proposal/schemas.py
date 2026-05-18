"""Proposal Generation Schemas"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, Any, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    DRAFT = 'draft'
    GENERATING = 'generating'
    COMPLETED = 'completed'
    REVIEWING = 'reviewing'
    APPROVED = 'approved'
    SUBMITTED = 'submitted'
    REJECTED = 'rejected'
    ARCHIVED = 'archived'


class SectionType(str, Enum):
    EXECUTIVE_SUMMARY = 'executive_summary'
    COMPANY_PROFILE = 'company_profile'
    UNDERSTANDING = 'understanding'
    APPROACH = 'approach'
    METHODOLOGY = 'methodology'
    TEAM = 'team'
    TIMELINE = 'timeline'
    PRICING = 'pricing'
    TERMS = 'terms'
    APPENDICES = 'appendices'
    COVER = 'cover'
    TABLE_OF_CONTENTS = 'table_of_contents'


class ProposalSection(BaseModel):
    section_id: str = Field(default_factory=lambda: str(uuid4()))
    section_type: SectionType = SectionType.EXECUTIVE_SUMMARY
    title: str = Field(..., description="Section title")
    content: str = Field(default='', description="Section content (markdown or HTML)")
    order: int = 0

    is_generated: bool = Field(default=False)
    is_edited: bool = Field(default=False)
    is_locked: bool = Field(default=False)

    word_count: int = 0
    confidence_score: float = Field(default=0.0, ge=0, le=1)

    required_for_submission: bool = Field(default=True)
    editable: bool = Field(default=True)

    version: int = Field(default=1)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class CompanyProfile(BaseModel):
    profile_id: str = Field(default_factory=lambda: str(uuid4()))
    company_name: str
    registration_number: Optional[str] = None

    tagline: Optional[str] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[str] = None

    headquarters: Optional[str] = None
    addresses: list[str] = Field(default_factory=list)
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    certifications: list[str] = Field(default_factory=list)
    accreditations: list[str] = Field(default_factory=list)
    memberships: list[str] = Field(default_factory=list)

    sectors: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    key_clients: list[str] = Field(default_factory=list)

    achievements: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)

    financials_summary: Optional[str] = None
    annual_turnover: Optional[str] = None

    values: list[str] = Field(default_factory=list)
    mission: Optional[str] = None
    vision: Optional[str] = None

    logo_url: Optional[str] = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class TeamMember(BaseModel):
    member_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    designation: str
    qualification: Optional[str] = None
    experience_years: Optional[int] = None

    role_in_project: str
    responsibilities: list[str] = Field(default_factory=list)
    key_qualifications: list[str] = Field(default_factory=list)

    photo_url: Optional[str] = None
    linkedin_url: Optional[str] = None


class ExperienceProject(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    client_name: str
    project_title: str
    project_value: Optional[str] = None

    description: str
    scope: str
    outcome: Optional[str] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_months: Optional[int] = None

    location: Optional[str] = None
    is_similar: bool = Field(default=False, description="Similar to current tender")

    references: list[str] = Field(default_factory=list)


class CompanyIntelligence(BaseModel):
    intelligence_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: Optional[UUID] = None

    company_profile: Optional[CompanyProfile] = None
    team_members: list[TeamMember] = Field(default_factory=list)
    past_projects: list[ExperienceProject] = Field(default_factory=list)

    capabilities: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)
    value_propositions: list[str] = Field(default_factory=list)

    proposal_templates: list[dict] = Field(default_factory=list)
    reusable_sections: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    is_active: bool = Field(default=True)
    version: int = Field(default=1)


class PricingItem(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    quantity: Optional[str] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    currency: str = 'INR'

    category: str = Field(default='service', description="service, material, labor, overhead")
    is_optional: bool = Field(default=False)
    notes: Optional[str] = None


class ProposalPricing(BaseModel):
    items: list[PricingItem] = Field(default_factory=list)
    subtotal: float = Field(default=0.0)
    tax_percentage: float = Field(default=18.0)
    tax_amount: float = Field(default=0.0)
    discount_percentage: float = Field(default=0.0)
    discount_amount: float = Field(default=0.0)
    grand_total: float = Field(default=0.0)
    currency: str = 'INR'

    payment_terms: Optional[str] = None
    validity_days: int = Field(default=30)


class ProposalDraft(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    tender_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None

    title: str = Field(..., description="Proposal title")
    reference_number: Optional[str] = None

    status: ProposalStatus = ProposalStatus.DRAFT

    sections: list[ProposalSection] = Field(default_factory=list)

    company_intelligence: Optional[CompanyIntelligence] = None
    pricing: Optional[ProposalPricing] = None

    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None

    created_by: Optional[str] = None
    modified_by: Optional[str] = None

    total_words: int = 0
    estimated_pages: int = 0

    compliance_score: float = Field(default=0.0, ge=0, le=100)

    metadata: dict[str, Any] = Field(default_factory=dict)


class RegenerationRequest(BaseModel):
    section_id: Optional[str] = None
    section_types: Optional[List[str]] = None
    prompt_override: Optional[str] = None
    keep_existing_content: bool = Field(default=False)
    style: Optional[str] = Field(default='professional', description="professional, concise, detailed")


class ProposalGenerationRequest(BaseModel):
    tender_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    document_text: str = Field(..., min_length=100)
    company_intelligence_id: Optional[str] = None

    title: Optional[str] = None
    include_sections: Optional[List[str]] = None
    exclude_sections: Optional[List[str]] = None

    style: str = Field(default='professional')
    tone: str = Field(default='formal')
    length: str = Field(default='medium', description="short, medium, detailed")


class ProposalGenerationResponse(BaseModel):
    proposal_id: str
    status: ProposalStatus
    title: str
    sections_generated: int
    total_words: int
    generation_time_ms: int
    confidence: float
    warnings: list[str]


class SectionUpdateRequest(BaseModel):
    section_id: str
    content: str
    edited_by: Optional[str] = None


class ProposalExportFormat(str, Enum):
    DOCX = 'docx'
    PDF = 'pdf'
    HTML = 'html'
    MARKDOWN = 'markdown'
    JSON = 'json'


class ProposalExportConfig(BaseModel):
    format: ProposalExportFormat = ProposalExportFormat.DOCX
    include_cover: bool = True
    include_toc: bool = True
    include_appendices: bool = True
    include_pricing: bool = True
    include_company_profile: bool = True

    page_size: str = Field(default='A4')
    font_size: int = Field(default=11)
    font_family: str = Field(default='Calibri')

    add_page_numbers: bool = True
    add_header_footer: bool = True
    header_text: Optional[str] = None
    footer_text: Optional[str] = None

    template_id: Optional[str] = None