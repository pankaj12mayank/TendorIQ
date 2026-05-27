"""SQLAlchemy Database Models for TenderIQ"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

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


def pk_str(value: str | UUID) -> str:
    """Normalize primary keys for String(36) UUID columns (SQLite-safe)."""
    return str(value)


def utc_now() -> datetime:
    return datetime.utcnow()


class TenantMixin:
    """Legacy workspace column — kept for storage paths until full tenant removal."""

    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)


class OwnerMixin:
    """Lite MVP: primary data isolation by user."""

    owner_id = Column(UuidCol, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)


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
    proposals = relationship('Proposal', back_populates='bidder', foreign_keys='[Proposal.bidder_id]')
    usage_logs = relationship('UsageLog', back_populates='user')
    company_profile = relationship(
        'CompanyProfile',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
    )


class CompanyProfile(Base, TimestampMixin):
    """Per-user company details (Lite MVP — replaces org onboarding)."""

    __tablename__ = 'company_profiles'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    company_name = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    tax_id = Column(String(100), nullable=True)
    logo_url = Column(Text, nullable=True)
    metadata_json = Column('metadata', JsonCol, default=dict)

    user = relationship('User', back_populates='company_profile')


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


class Tender(Base, TenantMixin, OwnerMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
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
        Index('idx_tender_owner_status', 'owner_id', 'status'),
        Index('idx_tender_tenant_status', 'tenant_id', 'status'),
        Index('idx_tender_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_tender_closing', 'closing_date'),
        Index('idx_tender_type', 'tender_type'),
        CheckConstraint("status IN ('draft', 'published', 'closed', 'cancelled', 'awarded')", name='valid_tender_status'),
    )

    tenant = relationship('Tenant', back_populates='tenders')
    proposals = relationship('Proposal', back_populates='tender', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='tender', cascade='all, delete-orphan')
    analysis_results = relationship('AnalysisResult', back_populates='tender', cascade='all, delete-orphan')



class Document(Base, TenantMixin, OwnerMixin, TimestampMixin, SoftDeleteMixin):
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
        Index('idx_document_owner_created', 'owner_id', 'created_at'),
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


class AnalysisResult(Base, TenantMixin, OwnerMixin, TimestampMixin):
    """AI Analysis Results"""

    __tablename__ = 'analysis_results'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=True, index=True)
    document_id = Column(UuidCol, ForeignKey('documents.id', ondelete='CASCADE'), nullable=True, index=True)

    analysis_type = Column(String(50), nullable=False)

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
        CheckConstraint("analysis_type IN ('tender_summary', 'bid_review', 'risk_assessment', 'compliance', 'scoring')", name='valid_analysis_type'),
    )

    tender = relationship('Tender', back_populates='analysis_results')
    document = relationship('Document', back_populates='analysis_results')




class Proposal(Base, TenantMixin, OwnerMixin, TimestampMixin, AuditMixin):
    """Proposal/Quote submissions"""

    __tablename__ = 'proposals'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tender_id = Column(UuidCol, ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False, index=True)

    bidder_id = Column(UuidCol, ForeignKey('users.id'), nullable=False)

    amount = Column(Float, nullable=True)
    currency = Column(String(3), default='USD')

    description = Column(Text, nullable=True)
    timeline_days = Column(Integer, nullable=True)

    title = Column(String(500), nullable=True)
    sections_json = Column(JsonCol, default=dict)
    model_used = Column(String(100), nullable=True)

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


class PlatformSetting(Base):
    """Key-value platform configuration (pricing, landing CMS, AI defaults)."""

    __tablename__ = 'platform_settings'

    key = Column(String(64), primary_key=True)
    value_json = Column(JsonCol, default={})
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PasswordResetToken(Base, TimestampMixin):
    """One-time password reset token entries (hashed token only)."""

    __tablename__ = 'password_reset_tokens'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    requested_ip = Column(String(45), nullable=True)

    __table_args__ = (
        Index('idx_password_reset_user_active', 'user_id', 'expires_at', 'used_at'),
    )


class PaymentTransaction(Base, TenantMixin, TimestampMixin):
    """Admin-visible payment ledger for all gateways."""

    __tablename__ = 'payment_transactions'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    subscription_id = Column(UuidCol, ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True, index=True)
    provider = Column(String(32), nullable=False, index=True)  # razorpay | stripe
    order_id = Column(String(128), nullable=True, index=True)
    payment_id = Column(String(128), nullable=True, index=True)
    external_customer_id = Column(String(128), nullable=True, index=True)
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(8), nullable=False, default='INR')
    plan = Column(String(64), nullable=True, index=True)
    status = Column(String(32), nullable=False, default='created', index=True)
    failure_reason = Column(Text, nullable=True)
    metadata_json = Column('metadata', JsonCol, default=dict)
    paid_at = Column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint('provider', 'payment_id', name='uq_payment_provider_payment_id'),
        UniqueConstraint('provider', 'order_id', name='uq_payment_provider_order_id'),
        Index('idx_payments_tenant_status_created', 'tenant_id', 'status', 'created_at'),
        Index('idx_payments_tenant_provider_created', 'tenant_id', 'provider', 'created_at'),
        CheckConstraint("provider IN ('razorpay', 'stripe')", name='valid_payment_provider'),
        CheckConstraint("status IN ('created', 'paid', 'failed', 'refunded')", name='valid_payment_status'),
    )


