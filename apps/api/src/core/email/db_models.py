"""Email system database models — event-driven transactional email infrastructure."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from ..db_types import JsonCol, UuidCol
from ..models import Base, TimestampMixin, generate_uuid


class EmailTemplate(Base, TimestampMixin):
    __tablename__ = 'email_templates'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    slug = Column(String(120), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text, nullable=True)
    variables = Column(JsonCol, default=list)
    variable_defaults = Column(JsonCol, default=dict)
    status = Column(String(20), nullable=False, default='active', index=True)  # active | inactive | archived
    version = Column(Integer, nullable=False, default=1)
    parent_id = Column(UuidCol, ForeignKey('email_templates.id'), nullable=True)
    sender_name = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)
    preview_text = Column(String(255), nullable=True)
    branding = Column(JsonCol, default=dict)
    created_by_id = Column(UuidCol, nullable=True)
    updated_by_id = Column(UuidCol, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index('ix_email_templates_slug_tenant', 'slug', 'tenant_id'),
    )


class EmailEvent(Base, TimestampMixin):
    __tablename__ = 'email_events'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    event_key = Column(String(120), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(60), nullable=False, index=True)
    description = Column(Text, nullable=True)
    template_id = Column(UuidCol, ForeignKey('email_templates.id', ondelete='SET NULL'), nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=True)
    event_meta = Column(JsonCol, default=dict)

    __table_args__ = (
        Index('ix_email_events_key_tenant', 'event_key', 'tenant_id', unique=True),
    )


class EmailBranding(Base, TimestampMixin):
    __tablename__ = 'email_branding'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, unique=True)
    logo_url = Column(Text, nullable=True)
    primary_color = Column(String(20), default='#2563eb')
    accent_color = Column(String(20), default='#7c3aed')
    footer_html = Column(Text, nullable=True)
    company_name = Column(String(255), default='TenderIQ')
    support_email = Column(String(255), default='support@tenderiq.com')
    website_url = Column(String(500), nullable=True)
    social_links = Column(JsonCol, default=dict)


class SmtpConfig(Base, TimestampMixin):
    __tablename__ = 'smtp_configs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    name = Column(String(120), nullable=False, default='Primary SMTP')
    provider = Column(String(30), nullable=False, default='smtp')  # smtp | resend
    host = Column(String(255), nullable=True)
    port = Column(Integer, default=587)
    username = Column(String(255), nullable=True)
    password_encrypted = Column(Text, nullable=True)
    encryption = Column(String(20), default='tls')  # tls | ssl | none
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=False, default='TenderIQ')
    is_primary = Column(Boolean, default=False)
    is_fallback = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_status = Column(String(30), nullable=True)


class FirebaseConfig(Base, TimestampMixin):
    __tablename__ = 'firebase_configs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, unique=True)
    project_id = Column(String(255), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    auth_domain = Column(String(255), nullable=True)
    app_id = Column(String(255), nullable=True)
    reset_url = Column(String(500), nullable=True)
    verify_url = Column(String(500), nullable=True)
    dynamic_link_domain = Column(String(255), nullable=True)
    is_enabled = Column(Boolean, default=False)
    use_for_auth_emails = Column(Boolean, default=False)


class EmailQueueItem(Base, TimestampMixin):
    __tablename__ = 'email_queue'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    template_id = Column(UuidCol, ForeignKey('email_templates.id'), nullable=True)
    event_name = Column(String(120), nullable=True, index=True)
    subject = Column(String(500), nullable=True)
    html_body = Column(Text, nullable=True)
    variables = Column(JsonCol, default=dict)
    status = Column(String(30), nullable=False, default='pending', index=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now())
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    provider_name = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    priority = Column(Integer, default=5)
    log_id = Column(UuidCol, ForeignKey('email_logs.id'), nullable=True)


class EmailLog(Base, TimestampMixin):
    __tablename__ = 'email_logs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    tenant_id = Column(UuidCol, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    template_id = Column(UuidCol, ForeignKey('email_templates.id'), nullable=True)
    event_name = Column(String(120), nullable=True, index=True)
    subject = Column(String(500), nullable=False)
    status = Column(String(30), nullable=False, default='pending', index=True)
    retry_count = Column(Integer, default=0)
    message_id = Column(String(255), nullable=True)
    provider_name = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    log_meta = Column(JsonCol, default=dict)


class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    user_id = Column(UuidCol, ForeignKey('users.id'), nullable=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
