"""Document Management Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProcessingStatus:
    UPLOADED = 'uploaded'
    PROCESSING = 'processing'
    RETRYING = 'retrying'
    COMPLETED = 'completed'
    FAILED = 'failed'
    NEEDS_REVIEW = 'needs_review'
    DELETED = 'deleted'

    ALL = [UPLOADED, PROCESSING, RETRYING, COMPLETED, FAILED, NEEDS_REVIEW, DELETED]


class DocumentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    file_name: str = Field(..., min_length=1, max_length=500)
    file_type: str = Field(..., max_length=100)
    file_size: int = Field(..., ge=1)
    storage_key: str = Field(..., max_length=1000)
    mime_type: Optional[str] = Field(None, max_length=100)
    checksum: Optional[str] = Field(None, max_length=64)
    tender_id: Optional[str] = None
    folder: Optional[str] = Field(None, max_length=255)
    tags: list[str] = Field(default_factory=list)
    category: str = Field(default='documents')
    metadata: dict = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    folder: Optional[str] = Field(None, max_length=255)
    tags: Optional[list[str]] = None
    is_public: Optional[bool] = None
    metadata: Optional[dict] = None


class ProcessingStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(uploaded|processing|retrying|completed|failed|needs_review)$')
    error_message: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[dict] = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    tender_id: Optional[str] = None
    name: str
    file_name: str
    file_type: str
    file_size: int
    storage_key: str
    storage_provider: str
    storage_path: Optional[str] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None

    processing_status: str = 'uploaded'
    processing_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    metadata: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    folder: Optional[str] = None
    category: Optional[str] = None

    is_public: bool = False
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    id: str
    name: str
    file_name: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    processing_status: str
    retry_count: int
    folder: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    success: bool = True
    documents: list[DocumentListItem]
    total: int
    page: int
    limit: int
    pages: int


class DocumentFilter(BaseModel):
    search: Optional[str] = Field(None, max_length=200)
    status: Optional[list[str]] = Field(None)
    file_type: Optional[list[str]] = Field(None)
    tender_id: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[list[str]] = Field(None)
    is_archived: bool = False
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = 'created_at'
    sort_order: str = 'desc'


class QuotaCheckRequest(BaseModel):
    file_size: int = Field(..., ge=1)
    file_count_add: int = Field(default=1, ge=1)


class QuotaCheckResponse(BaseModel):
    allowed: bool
    current_storage_mb: float
    current_files: int
    quota_storage_mb: int
    quota_files: int
    storage_remaining_mb: float
    files_remaining: int
    upgrade_required: bool = False


class RetryRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)


class RetryResponse(BaseModel):
    success: bool = True
    retried_count: int
    skipped_count: int
    errors: list[str] = Field(default_factory=list)


class BatchStatusUpdate(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)
    status: str = Field(..., pattern=r'^(archived|restored|deleted)$')


class BatchUpdateResponse(BaseModel):
    success: bool = True
    updated_count: int
    errors: list[str] = Field(default_factory=list)


class DocumentStats(BaseModel):
    total_documents: int
    total_size_bytes: int
    total_size_mb: float
    by_status: dict[str, int]
    by_type: dict[str, int]
    failed_count: int
    needs_review_count: int
    pending_count: int
    quota_usage_percent: float


class DocumentStatsResponse(BaseModel):
    success: bool = True
    tenant_id: str
    stats: DocumentStats