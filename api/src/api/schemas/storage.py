"""Storage and File Upload Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FileUploadRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., ge=1)
    content_type: Optional[str] = Field(None, max_length=100)
    tender_id: Optional[str] = None
    category: str = Field(default='documents', pattern=r'^[a-z_]+$')


class FileUploadResponse(BaseModel):
    success: bool = True
    document_id: str
    storage_key: str
    upload_url: Optional[str] = None
    expires_at: Optional[str] = None
    expires_in: Optional[int] = None


class FileDownloadRequest(BaseModel):
    document_id: str


class FileDownloadResponse(BaseModel):
    success: bool = True
    document_id: str
    download_url: str
    expires_at: str
    expires_in: int
    file_name: str
    file_size: int
    content_type: Optional[str] = None


class FileMetadataResponse(BaseModel):
    success: bool = True
    document: 'DocumentResponse'


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
    is_public: bool = False
    expires_at: Optional[datetime] = None
    is_archived: bool = False
    access_count: int = 0
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class FileListResponse(BaseModel):
    success: bool = True
    files: list[DocumentResponse]
    total: int
    page: int
    limit: int
    pages: int


class FileDeleteRequest(BaseModel):
    document_id: str
    permanently: bool = Field(default=False)


class FileDeleteResponse(BaseModel):
    success: bool = True
    document_id: str
    deleted: bool
    storage_deleted: bool


class BatchFileDeleteRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)


class BatchFileDeleteResponse(BaseModel):
    success: bool = True
    deleted_count: int
    failed_count: int
    errors: list[str] = Field(default_factory=list)


class SignedUrlRequest(BaseModel):
    document_id: str
    url_type: str = Field(..., pattern=r'^(upload|download)$')
    expires_seconds: Optional[int] = Field(None, ge=60, le=86400)


class SignedUrlResponse(BaseModel):
    success: bool = True
    url: str
    storage_key: str
    expires_at: str
    expires_in: int
    url_type: str


class FileValidationError(BaseModel):
    field: str
    message: str


class FileValidationResponse(BaseModel):
    valid: bool
    errors: list[FileValidationError] = Field(default_factory=list)


class StorageStatsResponse(BaseModel):
    success: bool = True
    tenant_id: str
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    by_type: dict[str, int]
    by_category: dict[str, int]


class FileArchiveRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)


class FileArchiveResponse(BaseModel):
    success: bool = True
    archived_count: int
    errors: list[str] = Field(default_factory=list)