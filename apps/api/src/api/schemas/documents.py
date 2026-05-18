"""Document Management Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


PROCESSING_STATUSES = ['uploaded', 'processing', 'retrying', 'completed', 'failed', 'needs_review', 'deleted']


class DocumentStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(uploaded|processing|retrying|completed|failed|needs_review)$')
    error_message: Optional[str] = None


class DocumentCreateRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., ge=1)
    content_type: Optional[str] = Field(None, max_length=100)
    tender_id: Optional[str] = None
    category: str = Field(default='documents', pattern=r'^[a-z_]+$')
    tags: list[str] = Field(default_factory=list)
    folder: Optional[str] = Field(None, max_length=255)


class DocumentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    tags: Optional[list[str]] = None
    folder: Optional[str] = Field(None, max_length=255)
    is_public: Optional[bool] = None
    expires_at: Optional[datetime] = None


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
    processing_status: str
    processing_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    folder: Optional[str] = None
    is_public: bool = False
    expires_at: Optional[datetime] = None
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    success: bool = True
    documents: list[DocumentResponse]
    total: int
    page: int
    limit: int
    pages: int


class DocumentFilterRequest(BaseModel):
    status: Optional[str] = Field(None, pattern=r'^(uploaded|processing|retrying|completed|failed|needs_review)$')
    tender_id: Optional[str] = None
    file_type: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[list[str]] = None
    search: Optional[str] = Field(None, max_length=255)
    is_archived: bool = False
    include_deleted: bool = False


class DocumentRetryRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)
    reset_retry_count: bool = Field(default=False)


class DocumentBatchUpdateRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)
    action: str = Field(..., pattern=r'^(archive|unarchive|delete|tag|folder)$')
    value: Optional[str] = None
    tags: Optional[list[str]] = None


class DocumentQuotaResponse(BaseModel):
    success: bool = True
    tenant_id: str
    current_files: int
    current_size_bytes: int
    current_size_mb: float
    max_files: int
    max_size_mb: int
    files_used_percent: float
    size_used_percent: float
    can_upload: bool
    message: str


class DocumentProcessingStatus(BaseModel):
    document_id: str
    status: str
    progress: int = 0
    error: Optional[str] = None
    retry_count: int = 0
    can_retry: bool


class DocumentProcessingStatusBatch(BaseModel):
    success: bool = True
    statuses: list[DocumentProcessingStatus]


class UploadInitResponse(BaseModel):
    success: bool = True
    document_id: str
    storage_key: str
    upload_url: Optional[str] = None
    expires_at: Optional[str] = None
    expires_in: Optional[int] = None
    quota_check: DocumentQuotaResponse


class DocumentDeleteResponse(BaseModel):
    success: bool = True
    document_id: str
    permanently: bool
    storage_deleted: bool


class DocumentBatchDeleteResponse(BaseModel):
    success: bool = True
    deleted_count: int
    failed_count: int
    permanently: bool
    errors: list[str] = Field(default_factory=list)


class DocumentStatsResponse(BaseModel):
    success: bool = True
    total: int
    by_status: dict[str, int]
    by_type: dict[str, int]
    total_size_bytes: int
    total_size_mb: float