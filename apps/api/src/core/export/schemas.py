"""Export Engine - Data Models and Schemas"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    PDF = 'pdf'
    DOCX = 'docx'
    MARKDOWN = 'markdown'
    HTML = 'html'
    JSON = 'json'
    CSV = 'csv'


class ExportStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    EXPIRED = 'expired'


class ExportType(str, Enum):
    PROPOSAL = 'proposal'
    CHECKLIST = 'checklist'
    RISK_ANALYSIS = 'risk_analysis'
    TENDER_DOCUMENT = 'tender_document'
    REPORT = 'report'
    INVOICE = 'invoice'
    CUSTOM = 'custom'


class WatermarkPosition(str, Enum):
    DIAGONAL = 'diagonal'
    CENTER = 'center'
    CORNER = 'corner'
    TILE = 'tile'


class ExportWatermark(BaseModel):
    text: str
    opacity: float = Field(default=0.1, ge=0.0, le=1.0)
    font_size: int = 24
    color: str = '#808080'
    position: WatermarkPosition = WatermarkPosition.DIAGONAL
    diagonal_angle: int = 45


class ExportTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    logo_url: Optional[str] = None
    logo_position: str = 'top-left'
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    primary_color: str = '#3182ce'
    secondary_color: str = '#718096'
    accent_color: str = '#2c5282'
    font_family: str = 'Segoe UI'
    font_size: int = 11
    show_page_numbers: bool = True
    show_timestamp: bool = True
    show_watermark: bool = False
    watermark: Optional[ExportWatermark] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ExportMetadata(BaseModel):
    export_id: str = Field(default_factory=lambda: str(uuid4()))
    export_type: ExportType
    format: ExportFormat
    title: str
    description: Optional[str] = None
    generated_by: str
    organization_id: str
    tenant_id: str
    source_id: str
    source_type: str
    template_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    checksum: Optional[str] = None


class ExportRequest(BaseModel):
    export_type: ExportType
    format: ExportFormat
    source_id: str
    source_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[str] = None
    include_watermark: bool = False
    include_logo: bool = True
    include_timestamp: bool = True
    include_pagination: bool = True
    include_metadata: bool = True
    compression_enabled: bool = False
    password_protected: bool = False
    metadata_filters: Optional[dict[str, Any]] = None


class ExportJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    export_id: str
    status: ExportStatus = ExportStatus.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    export_type: ExportType
    format: ExportFormat
    source_id: str
    source_type: str
    requested_by: str
    organization_id: str
    template_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None


class ExportResponse(BaseModel):
    export_id: str
    status: ExportStatus
    download_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    format: ExportFormat
    created_at: datetime
    expires_at: Optional[datetime] = None


class ExportLog(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid4()))
    export_id: str
    action: str
    user_id: str
    organization_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExportStatistics(BaseModel):
    total_exports: int = 0
    pdf_exports: int = 0
    docx_exports: int = 0
    other_exports: int = 0
    total_size_bytes: int = 0
    avg_processing_time_seconds: float = 0.0
    success_rate: float = 0.0
    by_organization: dict[str, int] = {}
    by_user: dict[str, int] = {}