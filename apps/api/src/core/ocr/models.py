"""OCR Result Model"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    ForeignKey, Index, JSON, func,
)
from ..db_types import UuidCol
from sqlalchemy.orm import relationship

from .models import Base, TenantMixin, TimestampMixin


def generate_uuid() -> str:
    return str(uuid4())


class OCRResult(Base, TenantMixin):
    """OCR extraction results"""

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

    metadata_json = Column('metadata', JSON, default=dict)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_ocr_document', 'document_id'),
        Index('idx_ocr_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_ocr_status', 'status'),
        Index('idx_ocr_confidence', 'confidence_score'),
    )

    document = relationship('Document', back_populates='ocr_results')


class OCRJob(Base, TenantMixin, TimestampMixin):
    """OCR job tracking"""

    __tablename__ = 'ocr_jobs'

    id = Column(UuidCol, primary_key=True, default=generate_uuid)
    document_id = Column(UuidCol, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)

    arq_job_id = Column(String(255), nullable=True, unique=True, index=True)
    status = Column(String(20), default='pending', index=True)

    priority = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    result_summary = Column(JSON, default=dict)

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