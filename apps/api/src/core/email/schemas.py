"""Email Schemas and Models"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class EmailType(str, Enum):
    UPLOAD_RECEIVED = 'upload_received'
    PROCESSING_COMPLETED = 'processing_completed'
    PROCESSING_FAILED = 'processing_failed'
    QUOTA_EXCEEDED = 'quota_exceeded'
    SUBSCRIPTION_ALERT = 'subscription_alert'
    GENERIC = 'generic'


class EmailStatus(str, Enum):
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    FAILED = 'failed'
    BOUNCED = 'bounced'


class EmailRequest(BaseModel):
    to: str | list[str]
    subject: str
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    template_type: Optional[EmailType] = None
    template_data: Optional[dict[str, Any]] = None
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    attachments: Optional[list[dict]] = None
    metadata: Optional[dict[str, Any]] = None


class EmailResponse(BaseModel):
    message_id: str
    status: EmailStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    provider: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class EmailLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    user_id: Optional[UUID] = None
    email_type: EmailType
    to_address: str
    from_address: str
    subject: str
    status: EmailStatus
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    channel: str = 'email'
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EmailTemplate(BaseModel):
    template_id: str
    name: str
    subject: str
    html_content: str
    text_content: str
    email_type: EmailType


class RetryConfig(BaseModel):
    max_retries: int = 3
    base_delay: int = 60
    max_delay: int = 3600
    exponential_base: int = 2


class EmailBatchRequest(BaseModel):
    emails: list[EmailRequest]
    batch_size: int = 10


class EmailStats(BaseModel):
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_bounced: int = 0
    by_type: dict[EmailType, int] = {}
    period_start: datetime
    period_end: datetime