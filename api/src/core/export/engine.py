"""Export Engine - Base Engine and Common Utilities"""

import hashlib
import io
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from PIL import Image

from .schemas import (
    ExportFormat,
    ExportJob,
    ExportMetadata,
    ExportRequest,
    ExportResponse,
    ExportStatus,
    ExportTemplate,
    ExportType,
    ExportWatermark,
)

logger = logging.getLogger(__name__)


class ExportEngine:
    _templates: dict[str, ExportTemplate] = {}
    _jobs: dict[str, ExportJob] = {}
    _exports: dict[str, ExportMetadata] = {}

    def __init__(self):
        self._storage_path = os.environ.get('EXPORT_STORAGE_PATH', '/tmp/exports')
        os.makedirs(self._storage_path, exist_ok=True)

    def register_template(self, template: ExportTemplate) -> ExportTemplate:
        template.updated_at = datetime.utcnow()
        self._templates[template.template_id] = template
        logger.info(f'Registered export template: {template.name} ({template.template_id})')
        return template

    def get_template(self, template_id: str) -> Optional[ExportTemplate]:
        return self._templates.get(template_id)

    def list_templates(self, organization_id: Optional[str] = None) -> list[ExportTemplate]:
        templates = list(self._templates.values())
        if organization_id:
            templates = [t for t in templates if t.is_active]
        return sorted(templates, key=lambda t: t.created_at, reverse=True)

    def create_export_job(self, request: ExportRequest, user_id: str, organization_id: str) -> ExportJob:
        job_id = str(uuid.uuid4())
        export_id = str(uuid.uuid4())

        expires_at = datetime.utcnow() + timedelta(hours=24)

        metadata = ExportMetadata(
            export_id=export_id,
            export_type=request.export_type,
            format=request.format,
            title=request.title or f'{request.export_type.value} Export',
            generated_by=user_id,
            organization_id=organization_id,
            tenant_id='',
            source_id=request.source_id,
            source_type=request.source_type,
            template_id=request.template_id,
            expires_at=expires_at,
        )
        self._exports[export_id] = metadata

        job = ExportJob(
            job_id=job_id,
            export_id=export_id,
            status=ExportStatus.PENDING,
            export_type=request.export_type,
            format=request.format,
            source_id=request.source_id,
            source_type=request.source_type,
            requested_by=user_id,
            organization_id=organization_id,
            template_id=request.template_id,
            expires_at=expires_at,
        )
        self._jobs[job_id] = job
        logger.info(f'Created export job: {job_id} ({request.export_type.value} -> {request.format.value})')
        return job

    def get_job(self, job_id: str) -> Optional[ExportJob]:
        return self._jobs.get(job_id)

    def get_export(self, export_id: str) -> Optional[ExportMetadata]:
        return self._exports.get(export_id)

    def update_job_status(self, job_id: str, status: ExportStatus, **kwargs) -> Optional[ExportJob]:
        job = self._jobs.get(job_id)
        if not job:
            return None

        job.status = status
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        if status == ExportStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in (ExportStatus.COMPLETED, ExportStatus.FAILED):
            job.completed_at = datetime.utcnow()

        self._jobs[job_id] = job

        if status == ExportStatus.COMPLETED:
            metadata = self._exports.get(job.export_id)
            if metadata:
                metadata.file_size_bytes = job.file_size_bytes
                self._exports[job.export_id] = metadata

        return job

    def _generate_checksum(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _get_file_path(self, job_id: str, export_id: str, format: ExportFormat) -> str:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'{export_id}_{timestamp}.{format.value}'
        return os.path.join(self._storage_path, filename)

    def sanitize_filename(self, name: str) -> str:
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '-', name)
        return name[:100]

    def format_timestamp(self, dt: Optional[datetime] = None) -> str:
        dt = dt or datetime.utcnow()
        return dt.strftime('%d %b %Y, %H:%M:%S UTC')

    def format_filesize(self, bytes_size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f'{bytes_size:.1f} {unit}'
            bytes_size /= 1024
        return f'{bytes_size:.1f} TB'


export_engine = ExportEngine()


def get_export_engine() -> ExportEngine:
    return export_engine


class TemplateManager:
    DEFAULT_TEMPLATE = ExportTemplate(
        template_id='default',
        name='Standard Report',
        primary_color='#3182ce',
        secondary_color='#718096',
        accent_color='#2c5282',
        font_family='Segoe UI',
        show_page_numbers=True,
        show_timestamp=True,
    )

    BRANDED_TEMPLATE = ExportTemplate(
        template_id='branded',
        name='Branded Document',
        logo_position='top-center',
        header_text='{company_name}',
        primary_color='#1a365d',
        secondary_color='#4a5568',
        accent_color='#3182ce',
        font_family='Segoe UI',
        show_page_numbers=True,
        show_timestamp=True,
        show_watermark=False,
    )

    CONFIDENTIAL_TEMPLATE = ExportTemplate(
        template_id='confidential',
        name='Confidential Document',
        primary_color='#c53030',
        secondary_color='#718096',
        accent_color='#742a2a',
        font_family='Segoe UI',
        show_page_numbers=True,
        show_timestamp=True,
        show_watermark=True,
        watermark=ExportWatermark(
            text='CONFIDENTIAL',
            opacity=0.15,
            font_size=36,
            color='#c53030',
            position='diagonal',
            diagonal_angle=45,
        ),
    )

    def get_default(self) -> ExportTemplate:
        return self.DEFAULT_TEMPLATE.copy(deep=True)

    def get_branded(self) -> ExportTemplate:
        return self.BRANDED_TEMPLATE.copy(deep=True)

    def get_confidential(self) -> ExportTemplate:
        return self.CONFIDENTIAL_TEMPLATE.copy(deep=True)

    def get_for_document_type(self, doc_type: ExportType) -> ExportTemplate:
        templates_map = {
            ExportType.PROPOSAL: self.BRANDED_TEMPLATE,
            ExportType.RISK_ANALYSIS: self.DEFAULT_TEMPLATE,
            ExportType.CHECKLIST: self.DEFAULT_TEMPLATE,
            ExportType.INVOICE: self.CONFIDENTIAL_TEMPLATE,
            ExportType.REPORT: self.BRANDED_TEMPLATE,
        }
        return templates_map.get(doc_type, self.DEFAULT_TEMPLATE).copy(deep=True)


template_manager = TemplateManager()


def get_template_manager() -> TemplateManager:
    return template_manager