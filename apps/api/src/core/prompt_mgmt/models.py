"""Prompt Management Database Models"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
    Index,
)
from ..db_types import UuidCol
from sqlalchemy.orm import relationship

from ..database import Base


class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'

    id = Column(UuidCol, primary_key=True, default=uuid4)
    tenant_id = Column(UuidCol, nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    prompt_type = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    variables = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_system = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    versions = relationship('PromptTemplateVersion', back_populates='template', cascade='all, delete-orphan')
    analytics = relationship('PromptAnalytics', back_populates='prompt', cascade='all, delete-orphan')
    audit_logs = relationship('PromptAuditLog', back_populates='prompt', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_prompt_name_tenant', 'name', 'tenant_id'),
    )


class PromptTemplateVersion(Base):
    __tablename__ = 'prompt_template_versions'

    id = Column(UuidCol, primary_key=True, default=uuid4)
    prompt_id = Column(UuidCol, ForeignKey('prompt_templates.id', ondelete='CASCADE'), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    system_message = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)
    guardrails = Column(JSON, nullable=True)
    examples = Column(JSON, nullable=True)
    model = Column(String(100), nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    top_p = Column(Float, nullable=True)
    frequency_penalty = Column(Float, nullable=True)
    presence_penalty = Column(Float, nullable=True)
    is_active = Column(Boolean, default=False, index=True)
    change_summary = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    template = relationship('PromptTemplate', back_populates='versions')
    analytics = relationship('PromptAnalytics', back_populates='version', cascade='all, delete-orphan')
    audit_logs = relationship('PromptAuditLog', back_populates='version', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('prompt_id', 'version', name='unique_prompt_version'),
    )


class PromptAnalytics(Base):
    __tablename__ = 'prompt_analytics'

    id = Column(UuidCol, primary_key=True, default=uuid4)
    prompt_id = Column(UuidCol, ForeignKey('prompt_templates.id', ondelete='CASCADE'), nullable=False, index=True)
    version_id = Column(UuidCol, ForeignKey('prompt_template_versions.id', ondelete='CASCADE'), nullable=False)
    tenant_id = Column(UuidCol, nullable=True, index=True)
    request_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    avg_latency_ms = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    avg_user_rating = Column(Float, nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    prompt = relationship('PromptTemplate', back_populates='analytics')
    version = relationship('PromptTemplateVersion', back_populates='analytics')

    __table_args__ = (
        UniqueConstraint('prompt_id', 'version_id', 'tenant_id', name='unique_prompt_version_tenant'),
    )


class PromptAuditLog(Base):
    __tablename__ = 'prompt_audit_log'

    id = Column(UuidCol, primary_key=True, default=uuid4)
    prompt_id = Column(UuidCol, ForeignKey('prompt_templates.id', ondelete='SET NULL'), nullable=True, index=True)
    version_id = Column(UuidCol, ForeignKey('prompt_template_versions.id', ondelete='SET NULL'), nullable=True, index=True)
    tenant_id = Column(UuidCol, nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    actor = Column(String(255), nullable=True, index=True)
    changes = Column(JSON, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    prompt = relationship('PromptTemplate', back_populates='audit_logs')
    version = relationship('PromptTemplateVersion', back_populates='audit_logs')


class AuditAction:
    CREATED = 'created'
    UPDATED = 'updated'
    DELETED = 'deleted'
    ACTIVATED = 'activated'
    DEACTIVATED = 'deactivated'
    ROLLED_BACK = 'rolled_back'
    CLONED = 'cloned'
    ANALYTICS_UPDATED = 'analytics_updated'