"""SQLAlchemy Database Models for TenderIQ"""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Integer,
    Float,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
    JSON,
    Enum,
    func,
)
from sqlalchemy.orm import DeclarativeBase, foreign, relationship

from .db_types import JsonCol, UuidCol

class Base(DeclarativeBase):
    pass


def generate_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.utcnow()


class TenantMixin:
    """Mixin for multi-tenant support"""

    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete support"""

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_id = Column(UuidCol, ForeignKey('users.id'), nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class AuditMixin:
    """Mixin for audit trail"""

    created_by_id = Column(UuidCol, ForeignKey('users.id'), nullable=False)
    updated_by_id = Column(UuidCol, ForeignKey('users.id'), nullable=True)


class Tenant(Base):
    """Organizations/Tenants table"""

    __tablename__ = 'tenants'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    logo_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    settings = Column(JsonCol, default={})

    plan = Column(String(50), default='free')
    status = Column(String(20), default='active')

    subscription_id = Column(String(255), nullable=True)
    subscription_status = Column(String(50), nullable=True)

    quota_documents = Column(Integer, default=100)
    quota_storage_mb = Column(Integer, default=1024)
    quota_users = Column(Integer, default=5)

    used_documents = Column(Integer, default=0)
    used_storage_mb = Column(Integer, default=0)
    used_users = Column(Integer, default=0)

    billing_cycle = Column(String(20), default='monthly')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_tenant_status', 'status'),
        Index('idx_tenant_plan', 'plan'),
        Index('idx_tenant_created', 'created_at'),
        CheckConstraint("plan IN ('free', 'starter', 'professional', 'enterprise')", name='valid_plan'),
        CheckConstraint("billing_cycle IN ('monthly', 'yearly')", name='valid_tenant_billing_cycle'),
    )

    memberships = relationship('Membership', back_populates='tenant', cascade='all, delete-orphan')
    users = relationship(
        'User',
        secondary='memberships',
        primaryjoin='Tenant.id == foreign(Membership.tenant_id)',
        secondaryjoin='User.id == foreign(Membership.user_id)',
        back_populates='tenants',
        viewonly=True,
    )
    documents = relationship('Document', back_populates='tenant', cascade='all, delete-orphan')
    tenders = relationship('Tender', back_populates='tenant', cascade='all, delete-orphan')
    subscriptions = relationship('Subscription', back_populates='tenant', cascade='all, delete-orphan')
    onboarding_states = relationship('OnboardingState', back_populates='tenant', cascade='all, delete-orphan')


class User(Base):
    """Users table"""

    __tablename__ = 'users'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    email = Column(String(500), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    # Profile hint only; authorization uses memberships.role (never store super_admin here).
    role = Column(String(20), default='member')

    clerk_id = Column(String(255), nullable=True, unique=True, index=True)

    preferences = Column(JsonCol, default={})

    email_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_user_email_verified', 'email_verified'),
        Index('idx_user_role', 'role'),
        Index('idx_user_created', 'created_at'),
        CheckConstraint("role IN ('owner', 'admin', 'manager', 'analyst', 'member', 'viewer')", name='valid_user_role'),
    )

    memberships = relationship(
        'Membership',
        back_populates='user',
        cascade='all, delete-orphan',
        foreign_keys='[Membership.user_id]',
    )
    tenants = relationship(
        'Tenant',
        secondary='memberships',
        primaryjoin='User.id == foreign(Membership.user_id)',
        secondaryjoin='Tenant.id == foreign(Membership.tenant_id)',
        back_populates='users',
        viewonly=True,
    )
    audit_logs = relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')
    onboarding_state = relationship('OnboardingState', back_populates='user', uselist=False, cascade='all, delete-orphan')
    bids = relationship('Bid', back_populates='bidder', foreign_keys='[Bid.bidder_id]')
    proposals = relationship('Proposal', back_populates='bidder', foreign_keys='[Proposal.bidder_id]')
    usage_logs = relationship('UsageLog', back_populates='user')


class Membership(Base):
    """Many-to-many relationship between users and tenants"""

    __tablename__ = 'memberships'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)

    role = Column(String(20), default='member')
    status = Column(String(20), default='active')

    invited_by_id = Column(UuidCol, ForeignKey('users.id'), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='unique_user_tenant'),
        Index('idx_membership_user', 'user_id'),
        Index('idx_membership_tenant', 'tenant_id'),
        CheckConstraint("role IN ('owner', 'admin', 'manager', 'analyst', 'member', 'viewer')", name='valid_membership_role'),
        CheckConstraint("status IN ('pending', 'active', 'suspended')", name='valid_membership_status'),
    )

    user = relationship('User', back_populates='memberships', foreign_keys=[user_id])
    tenant = relationship('Tenant', back_populates='memberships')


class Tender(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Tenders table"""

    __tablename__ = 'tenders'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default='draft', index=True)

    budget = Column(Float, nullable=True)
    currency = Column(String(3), default='USD')

    closing_date = Column(DateTime(timezone=True), nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    requirements = Column(JsonCol, default=[])
    specifications = Column(JsonCol, default={})

    ai_summary = Column(Text, nullable=True)

    tender_type = Column(String(50), default='open')
    evaluation_criteria = Column(JsonCol, default=[])

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_tender_tenant_status', 'tenant_id', 'status'),
        Index('idx_tender_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_tender_closing', 'closing_date'),
        Index('idx_tender_type', 'tender_type'),
        CheckConstraint("status IN ('draft', 'published', 'closed', 'cancelled', 'awarded')", name='valid_tender_status'),
    )

    tenant = relationship('Tenant', back_populates='tenders')
    bids = relationship('Bid', back_populates='tender', cascade='all, delete-orphan')
    proposals = relationship('Proposal', back_populates='tender', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='tender', cascade='all, delete-orphan')
    checklists = relationship('Checklist', back_populates='tender', cascade='all, delete-orphan')
    risks = relationship('Risk', back_populates='tender', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='tender', cascade='all, delete-orphan')
    analysis_results = relationship('AnalysisResult', back_populates='tender', cascade='all, delete-orphan')


class Bid(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Proposals/Bids table"""

    __tablename__ = 'bids'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False, index=True)

    bidder_id = Column(UuidCol, ForeignKey('users.id'), nullable=False)
    organization_name = Column(String(255), nullable=True)

    amount = Column(Float, nullable=True)
    currency = Column(String(3), default='USD')

    status = Column(String(20), default='draft', index=True)

    proposal = Column(Text, nullable=True)
    proposal_documents = Column(JsonCol, default=list)

    ai_analysis = Column(JsonCol, nullable=True)
    ai_score = Column(Float, nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_bid_tender_status', 'tender_id', 'status'),
        Index('idx_bid_bidder', 'bidder_id'),
        Index('idx_bid_submitted', 'submitted_at'),
        Index('idx_bid_tenant_tender', 'tenant_id', 'tender_id'),
        Index('idx_bid_tenant_status', 'tenant_id', 'status'),
        CheckConstraint("status IN ('draft', 'submitted', 'under_review', 'accepted', 'rejected', 'withdrawn')", name='valid_bid_status'),
    )

    tender = relationship('Tender', back_populates='bids')
    bidder = relationship('User', back_populates='bids', foreign_keys=[bidder_id])
    analysis_results = relationship('AnalysisResult', back_populates='bid', cascade='all, delete-orphan')


class Document(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Documents table"""

    __tablename__ = 'documents'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=True, index=True)

    name = Column(String(500), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)

    storage_key = Column(String(1000), nullable=False)
    storage_provider = Column(String(20), default='s3')
    storage_path = Column(String(2000), nullable=True)

    mime_type = Column(String(100), nullable=True)
    checksum = Column(String(64), nullable=True)

    processing_status = Column(
        String(30),
        default='uploaded',
        index=True,
    )
    processing_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    metadata_json = Column('metadata', JsonCol, default={})
    tags = Column(JsonCol, default=list)
    folder = Column(String(255), nullable=True, index=True)
    category = Column(String(100), nullable=True, default='documents')

    is_public = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_document_tender', 'tender_id'),
        Index('idx_document_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_document_type', 'file_type'),
        Index('idx_document_expires', 'expires_at'),
        Index('idx_document_archived', 'is_archived'),
        Index('idx_document_status', 'processing_status'),
        Index('idx_document_tenant_status', 'tenant_id', 'processing_status'),
        Index('idx_document_folder', 'folder'),
        CheckConstraint("processing_status IN ('uploaded', 'processing', 'retrying', 'completed', 'failed', 'needs_review', 'deleted')", name='valid_processing_status'),
    )

    tenant = relationship('Tenant', back_populates='documents')
    tender = relationship('Tender', back_populates='documents')
    chunks = relationship('DocumentChunk', back_populates='document', cascade='all, delete-orphan')
    ocr_results = relationship('OCRResult', back_populates='document', cascade='all, delete-orphan')
    ocr_jobs = relationship('OCRJob', back_populates='document', cascade='all, delete-orphan')
    analysis_results = relationship('AnalysisResult', back_populates='document', cascade='all, delete-orphan')
    parsed_documents = relationship('ParsedDocument', back_populates='document', cascade='all, delete-orphan')


class DocumentChunk(Base, TenantMixin, TimestampMixin):
    """Document chunks for vector search"""

    __tablename__ = 'document_chunks'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    document_id = Column(UuidCol, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    parsed_document_id = Column(UuidCol, nullable=True, index=True)

    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer, default=0)
    end_char = Column(Integer, default=0)
    start_page = Column(Integer, default=1)
    end_page = Column(Integer, default=1)
    section_path = Column(String(500), nullable=True)
    tokens = Column(Integer, default=0)

    embedding = Column(JsonCol, default=None)

    metadata_json = Column('metadata', JsonCol, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_chunk_document', 'document_id'),
        Index('idx_chunk_parsed', 'parsed_document_id'),
        UniqueConstraint('document_id', 'chunk_index', name='unique_chunk_order'),
    )

    document = relationship('Document', back_populates='chunks')


class AnalysisResult(Base, TenantMixin, TimestampMixin):
    """AI Analysis Results"""

    __tablename__ = 'analysis_results'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=True, index=True)
    bid_id = Column(UuidCol, ForeignKey('bids.id', ondelete='CASCADE'), nullable=True, index=True)
    document_id = Column(UuidCol, ForeignKey('documents.id', ondelete='CASCADE'), nullable=True, index=True)

    analysis_type = Column(String(50), nullable=False)

    prompt_version_id = Column(UuidCol, ForeignKey('prompt_versions.id'), nullable=True)

    result = Column(JsonCol, default={})
    summary = Column(Text, nullable=True)

    score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)

    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_analysis_tender', 'tender_id', 'analysis_type'),
        Index('idx_analysis_bid', 'bid_id', 'analysis_type'),
        CheckConstraint("analysis_type IN ('tender_summary', 'bid_review', 'risk_assessment', 'compliance', 'scoring')", name='valid_analysis_type'),
    )

    tender = relationship('Tender', back_populates='analysis_results')
    bid = relationship('Bid', back_populates='analysis_results')
    document = relationship('Document', back_populates='analysis_results')


class Checklist(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Checklists for tender evaluation"""

    __tablename__ = 'checklists'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    items = Column(JsonCol, default=[])

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tender = relationship('Tender', back_populates='checklists')


class Risk(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Risks associated with tenders"""

    __tablename__ = 'risks'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    category = Column(String(50), nullable=True)
    severity = Column(String(20), default='medium')
    probability = Column(String(20), default='medium')

    impact = Column(Float, nullable=True)
    mitigation = Column(Text, nullable=True)

    status = Column(String(20), default='identified')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_risk_tender', 'tender_id', 'severity'),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name='valid_risk_severity'),
        CheckConstraint("status IN ('identified', 'mitigated', 'accepted', 'closed')", name='valid_risk_status'),
    )

    tender = relationship('Tender', back_populates='risks')


class Proposal(Base, TenantMixin, TimestampMixin, AuditMixin):
    """Proposal/Quote submissions"""

    __tablename__ = 'proposals'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False, index=True)

    bidder_id = Column(UuidCol, ForeignKey('users.id'), nullable=False)

    amount = Column(Float, nullable=True)
    currency = Column(String(3), default='USD')

    description = Column(Text, nullable=True)
    timeline_days = Column(Integer, nullable=True)

    status = Column(String(20), default='draft')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_proposal_tender', 'tender_id', 'status'),
        Index('idx_proposal_bidder', 'bidder_id'),
        Index('idx_proposal_tenant', 'tenant_id'),
        Index('idx_proposal_tenant_tender', 'tenant_id', 'tender_id'),
    )

    tender = relationship('Tender', back_populates='proposals')
    bidder = relationship('User', back_populates='proposals', foreign_keys=[bidder_id])


class PromptVersion(Base, TenantMixin, TimestampMixin):
    """AI Prompt versioning"""

    __tablename__ = 'prompt_versions'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)

    prompt_type = Column(String(50), nullable=False, index=True)

    content = Column(Text, nullable=False)
    variables = Column(JsonCol, default=list)

    version = Column(Integer, nullable=False)

    is_active = Column(Boolean, default=False, index=True)
    is_default = Column(Boolean, default=False)

    description = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)

    model = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_prompt_type_active', 'prompt_type', 'is_active'),
        UniqueConstraint('tenant_id', 'prompt_type', 'version', name='unique_prompt_version'),
        CheckConstraint("prompt_type IN ('tender_summary', 'bid_review', 'risk_assessment', 'compliance_check', 'document_parse')", name='valid_prompt_type'),
    )


class QueueJob(Base, TenantMixin, TimestampMixin):
    """Queue/Background job tracking"""

    __tablename__ = 'queue_jobs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)

    job_type = Column(String(50), nullable=False, index=True)
    job_id = Column(String(255), nullable=True, unique=True, index=True)

    status = Column(String(20), default='pending', index=True)
    priority = Column(Integer, default=0)

    payload = Column(JsonCol, default={})
    result = Column(JsonCol, nullable=True)
    error = Column(Text, nullable=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_job_status_scheduled', 'status', 'scheduled_at'),
        Index('idx_job_type_status', 'job_type', 'status'),
        Index('idx_job_tenant_status', 'tenant_id', 'status'),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')", name='valid_job_status'),
    )


class UsageLog(Base, TenantMixin, TimestampMixin):
    """Usage tracking logs"""

    __tablename__ = 'usage_logs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UuidCol, nullable=True)

    metadata_json = Column('metadata', JsonCol, default={})

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    cost_usd = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_usage_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_usage_user_created', 'user_id', 'created_at'),
        Index('idx_usage_action', 'action', 'created_at'),
        Index('idx_usage_resource', 'resource_type', 'resource_id'),
    )

    user = relationship('User', back_populates='usage_logs')


class Subscription(Base, TenantMixin, TimestampMixin):
    """Subscription/Billing"""

    __tablename__ = 'subscriptions'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)

    plan = Column(String(50), nullable=False)
    status = Column(String(20), default='active', index=True)

    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    stripe_customer_id = Column(String(255), nullable=True)

    billing_cycle = Column(String(20), default='monthly')
    billing_date = Column(DateTime(timezone=True), nullable=True)

    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')

    features = Column(JsonCol, default={})
    metadata_json = Column('metadata', JsonCol, default={})

    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_sub_tenant_plan', 'tenant_id', 'plan'),
        Index('idx_sub_tenant_status', 'tenant_id', 'status'),
        CheckConstraint("plan IN ('free', 'starter', 'professional', 'enterprise')", name='valid_subscription_plan'),
        CheckConstraint("status IN ('active', 'trialing', 'past_due', 'cancelled', 'unpaid')", name='valid_subscription_status'),
        CheckConstraint("billing_cycle IN ('monthly', 'yearly')", name='valid_billing_cycle'),
    )

    tenant = relationship('Tenant', back_populates='subscriptions')


class AuditLog(Base, TenantMixin, TimestampMixin):
    """Audit trail for all changes"""

    __tablename__ = 'audit_logs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id'), nullable=True, index=True)

    action = Column(String(100), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UuidCol, nullable=True, index=True)
    resource_name = Column(String(255), nullable=True)

    changes = Column(JsonCol, default={})
    old_values = Column(JsonCol, default={})
    new_values = Column(JsonCol, default={})

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    request_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_audit_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_action_type', 'action_type', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id', 'created_at'),
    )

    user = relationship('User', back_populates='audit_logs')


class Notification(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Notifications for users"""

    __tablename__ = 'notifications'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)

    user_id = Column(UuidCol, ForeignKey('users.id'), nullable=False, index=True)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='SET NULL'), nullable=True, index=True)

    type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    data = Column(JsonCol, default={})

    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read', 'created_at'),
        Index('idx_notification_user_created', 'user_id', 'created_at'),
        Index('idx_notification_tender', 'tender_id', 'created_at'),
        Index('idx_notification_tenant_created', 'tenant_id', 'created_at'),
    )

    tender = relationship('Tender', back_populates='notifications')


class OnboardingState(Base, TimestampMixin):
    """Onboarding state tracking per user"""

    __tablename__ = 'onboarding_states'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id'), nullable=False, unique=True, index=True)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True, index=True)

    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=5)

    step_1_completed = Column(Boolean, default=False)
    step_2_completed = Column(Boolean, default=False)
    step_3_completed = Column(Boolean, default=False)
    step_4_completed = Column(Boolean, default=False)
    step_5_completed = Column(Boolean, default=False)

    step_1_data = Column(JsonCol, default={})
    step_2_data = Column(JsonCol, default={})
    step_3_data = Column(JsonCol, default={})
    step_4_data = Column(JsonCol, default={})
    step_5_data = Column(JsonCol, default={})

    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    last_step_completed = Column(Integer, nullable=True)
    metadata_json = Column('metadata', JsonCol, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_onboarding_user', 'user_id'),
        Index('idx_onboarding_tenant', 'tenant_id'),
    )

    user = relationship('User', back_populates='onboarding_state')
    tenant = relationship('Tenant', back_populates='onboarding_states')


class OCRResult(Base, TenantMixin):
    __tablename__ = 'ocr_results'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    document_id = Column(UuidCol, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)

    extracted_text = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    language = Column(String(10), default='en')

    is_low_quality = Column(Boolean, default=False)
    blur_score = Column(Float, nullable=True)
    brightness_score = Column(Float, nullable=True)
    contrast_score = Column(Float, nullable=True)
    overall_quality_score = Column(Float, nullable=True)

    processing_time_ms = Column(Integer, default=0)

    status = Column(String(20), default='pending', index=True)
    error_message = Column(Text, nullable=True)

    retry_count = Column(Integer, default=0)

    metadata_json = Column('metadata', JsonCol, default=dict)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_ocr_document', 'document_id'),
        Index('idx_ocr_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_ocr_status', 'status'),
        Index('idx_ocr_language', 'language'),
        Index('idx_ocr_confidence', 'confidence_score'),
    )

    document = relationship('Document', back_populates='ocr_results')


class OCRJob(Base, TenantMixin, TimestampMixin):
    __tablename__ = 'ocr_jobs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    document_id = Column(UuidCol, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)

    arq_job_id = Column(String(255), nullable=True, unique=True, index=True)
    status = Column(String(20), default='pending', index=True)

    priority = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    result_summary = Column(JsonCol, default=dict)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_ocrjob_document', 'document_id'),
        Index('idx_ocrjob_status', 'status'),
        Index('idx_ocrjob_arq', 'arq_job_id'),
    )

    document = relationship('Document', back_populates='ocr_jobs')


class ParsedDocument(Base, TenantMixin, TimestampMixin):
    __tablename__ = 'parsed_documents'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    document_id = Column(UuidCol, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)

    file_name = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)

    metadata_json = Column(JsonCol, default={})
    full_text = Column(Text, nullable=True)

    page_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)

    sections_json = Column(JsonCol, default=[])
    tables_json = Column(JsonCol, default=[])
    images_json = Column(JsonCol, default=[])
    links_json = Column(JsonCol, default=[])

    status = Column(String(20), default='pending', index=True)
    error_message = Column(Text, nullable=True)

    chunk_count = Column(Integer, default=0)
    chunking_strategy = Column(String(20), default='hybrid')

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_parsed_document', 'document_id'),
        Index('idx_parsed_status', 'status'),
    )

    document = relationship('Document', back_populates='parsed_documents')


# ---- Admin store tables (migrated from file store) ----


class AIProvider(Base):
    """Platform-level AI provider configuration (e.g., Ollama, OpenAI, Azure).
    No tenant isolation — these are global platform settings.
    """

    __tablename__ = 'ai_providers'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    provider_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    provider_type = Column(String(50), nullable=False, default='ollama')
    base_url = Column(String(500), nullable=True)
    api_key_enc = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    models = Column(JsonCol, default=list)
    settings = Column(JsonCol, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_ai_provider_type', 'provider_type'),
    )


class DismissedFailedJob(Base):
    """Tracks failed-job IDs that admins have dismissed (hidden from the UI).
    Covers both synthetic mock failures and real EmailQueueItem failures.
    """

    __tablename__ = 'dismissed_failed_jobs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Email system tables (registered on Base.metadata for Alembic)
from .email.db_models import (  # noqa: E402, F401
    EmailTemplate,
    EmailEvent,
    EmailBranding,
    SmtpConfig,
    FirebaseConfig,
    EmailQueueItem,
    EmailLog,
    PasswordResetToken,
)