"""OCR Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class OCRJobCreate(BaseModel):
    document_id: str
    language: str = 'en'
    priority: int = Field(default=0, ge=0, le=10)


class OCRJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    tenant_id: str
    status: str
    priority: int
    retry_count: int
    max_retries: int
    error_message: Optional[str] = None
    result_summary: dict = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OCRResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    tenant_id: str
    extracted_text: Optional[str] = None
    confidence_score: float
    word_count: int
    language: str
    is_low_quality: bool
    blur_score: Optional[float] = None
    brightness_score: Optional[float] = None
    contrast_score: Optional[float] = None
    overall_quality_score: Optional[float] = None
    processing_time_ms: int
    status: str
    error_message: Optional[str] = None
    retry_count: int
    metadata: dict = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OCRProgressResponse(BaseModel):
    success: bool = True
    document_id: str
    status: str
    progress_percent: int
    current_step: str
    estimated_time_remaining_seconds: Optional[int] = None


class OCRQueueResponse(BaseModel):
    success: bool = True
    job_id: str
    document_id: str
    status: str
    queued_at: datetime


class OCRStatusResponse(BaseModel):
    success: bool = True
    document_id: str
    ocr_status: str
    has_result: bool
    result: Optional[OCRResultResponse] = None
    job: Optional[OCRJobResponse] = None


class OCRRetryRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)


class OCRRetryResponse(BaseModel):
    success: bool = True
    retried_count: int
    skipped_count: int
    errors: list[str] = Field(default_factory=list)


class QualityAssessmentResponse(BaseModel):
    success: bool = True
    document_id: str
    blur_score: float
    brightness_score: float
    contrast_score: float
    overall_quality: float
    is_blurry: bool
    is_too_dark: bool
    is_too_bright: bool
    needs_enhancement: bool
    recommended_dpi: int
    estimated_ocr_accuracy: str