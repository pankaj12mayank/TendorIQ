"""Export Engine - API Router"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ...core.auth import AuthContext
from ...core.export.schemas import (
    ExportFormat,
    ExportRequest,
    ExportTemplate,
    ExportType,
)
from ...core.export.service import ExportService, get_export_service
from ..dependencies.rbac_deps import RequireApiAccess, require_tenant_member

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/exports',
    tags=['Export'],
    dependencies=[Depends(require_tenant_member)],
)


@router.post('/export')
async def create_export(
    request: ExportRequest,
    current_user: RequireApiAccess,
    service: ExportService = Depends(get_export_service),
):
    user_id = current_user.user_id
    organization_id = current_user.tenant_id or 'default'
    job = service.create_export(request, user_id, organization_id)

    processed_job = service.process_export(job.job_id)

    if processed_job.status.value == 'failed':
        raise HTTPException(status_code=500, detail=processed_job.error_message or 'Export failed')

    return {
        'export_id': processed_job.export_id,
        'job_id': processed_job.job_id,
        'status': processed_job.status.value,
        'format': processed_job.format.value,
        'download_url': processed_job.download_url,
        'file_size_bytes': processed_job.file_size_bytes,
        'created_at': processed_job.created_at.isoformat(),
    }


@router.get('/{export_id}/download')
async def download_export(
    export_id: str,
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    result = service.get_export_file(export_id)
    if not result:
        raise HTTPException(status_code=404, detail='Export not found or not ready')

    content, mime_type, filename = result

    return StreamingResponse(
        iter([content]),
        media_type=mime_type,
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(content)),
            'X-Export-Timestamp': datetime.utcnow().isoformat(),
        },
    )


@router.get('/jobs/{job_id}')
async def get_job_status(
    job_id: str,
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    job = service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Export job not found')

    return {
        'job_id': job.job_id,
        'export_id': job.export_id,
        'status': job.status.value,
        'progress': job.progress,
        'format': job.format.value,
        'file_size_bytes': job.file_size_bytes,
        'created_at': job.created_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error_message': job.error_message,
    }


@router.post('/templates')
async def create_template(
    template: ExportTemplate,
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    created = service.register_template(template)
    return created.model_dump()


@router.get('/templates')
async def list_templates(
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    templates = service.list_templates()
    return [t.model_dump() for t in templates]


@router.get('/templates/{template_id}')
async def get_template(
    template_id: str,
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    templates = service.list_templates()
    template = next((t for t in templates if t.template_id == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail='Template not found')
    return template.model_dump()


@router.post('/export/proposal/{proposal_id}')
async def export_proposal(
    proposal_id: str,
    format: ExportFormat = Query(ExportFormat.PDF),
    template_id: Optional[str] = Query(None),
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    user_id = current_user.user_id
    organization_id = current_user.tenant_id or 'default'
    request = ExportRequest(
        export_type=ExportType.PROPOSAL,
        format=format,
        source_id=proposal_id,
        source_type='proposal',
        template_id=template_id,
    )

    job = service.create_export(request, user_id, organization_id)
    processed_job = service.process_export(job.job_id)

    if processed_job.status.value == 'failed':
        raise HTTPException(status_code=500, detail=processed_job.error_message or 'Export failed')

    return {
        'export_id': processed_job.export_id,
        'status': processed_job.status.value,
        'format': processed_job.format.value,
        'download_url': processed_job.download_url,
        'file_size_bytes': processed_job.file_size_bytes,
    }


@router.post('/export/checklist/{checklist_id}')
async def export_checklist(
    checklist_id: str,
    format: ExportFormat = Query(ExportFormat.PDF),
    template_id: Optional[str] = Query(None),
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    user_id = current_user.user_id
    organization_id = current_user.tenant_id or 'default'
    request = ExportRequest(
        export_type=ExportType.CHECKLIST,
        format=format,
        source_id=checklist_id,
        source_type='checklist',
        template_id=template_id,
    )

    job = service.create_export(request, user_id, organization_id)
    processed_job = service.process_export(job.job_id)

    if processed_job.status.value == 'failed':
        raise HTTPException(status_code=500, detail=processed_job.error_message or 'Export failed')

    return {
        'export_id': processed_job.export_id,
        'status': processed_job.status.value,
        'format': processed_job.format.value,
        'download_url': processed_job.download_url,
        'file_size_bytes': processed_job.file_size_bytes,
    }


@router.post('/export/risk-analysis/{analysis_id}')
async def export_risk_analysis(
    analysis_id: str,
    format: ExportFormat = Query(ExportFormat.PDF),
    template_id: Optional[str] = Query(None),
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    user_id = current_user.user_id
    organization_id = current_user.tenant_id or 'default'
    request = ExportRequest(
        export_type=ExportType.RISK_ANALYSIS,
        format=format,
        source_id=analysis_id,
        source_type='risk_analysis',
        template_id=template_id,
    )

    job = service.create_export(request, user_id, organization_id)
    processed_job = service.process_export(job.job_id)

    if processed_job.status.value == 'failed':
        raise HTTPException(status_code=500, detail=processed_job.error_message or 'Export failed')

    return {
        'export_id': processed_job.export_id,
        'status': processed_job.status.value,
        'format': processed_job.format.value,
        'download_url': processed_job.download_url,
        'file_size_bytes': processed_job.file_size_bytes,
    }


@router.get('/history')
async def get_export_history(
    limit: int = Query(50, ge=1, le=200),
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    organization_id = current_user.tenant_id or 'default'
    history = service.get_export_history(organization_id, limit)
    return {
        'exports': [
            {
                'export_id': log.export_id,
                'action': log.action,
                'user_id': log.user_id,
                'timestamp': log.timestamp.isoformat(),
                'details': log.details,
            }
            for log in history
        ],
        'total': len(history),
    }


@router.post('/batch')
async def batch_export(
    exports: list[ExportRequest],
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    if len(exports) > 10:
        raise HTTPException(status_code=400, detail='Maximum 10 exports per batch')

    user_id = current_user.user_id
    organization_id = current_user.tenant_id or 'default'
    results = []
    for export_req in exports:
        job = service.create_export(export_req, user_id, organization_id)
        processed_job = service.process_export(job.job_id)
        results.append({
            'export_id': processed_job.export_id,
            'status': processed_job.status.value,
            'format': processed_job.format.value,
            'download_url': processed_job.download_url,
        })

    return {'batch_id': f'batch_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}', 'results': results}


@router.post('/secure')
async def create_secure_export(
    request: ExportRequest,
    password: str = Query(...),
    service: ExportService = Depends(get_export_service),
    current_user: AuthContext = Depends(get_current_user),
):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters')

    user_id = current_user.user_id
    organization_id = current_user.tenant_id or 'default'
    job = service.create_export(request, user_id, organization_id)

    return {
        'job_id': job.job_id,
        'status': job.status.value,
        'message': 'Secure export created. PDF encryption available for enterprise plans.',
        'encryption_note': 'For full PDF encryption, upgrade to Enterprise plan.',
    }


@router.get('/formats')
async def get_supported_formats():
    return {
        'formats': [
            {
                'id': f.value,
                'name': f.value.upper(),
                'description': _get_format_description(f),
                'supported_for': _get_format_support(f),
            }
            for f in ExportFormat
        ]
    }


def _get_format_description(fmt: ExportFormat) -> str:
    descriptions = {
        ExportFormat.PDF: 'Adobe PDF format - best for printing and sharing',
        ExportFormat.DOCX: 'Microsoft Word format - editable document',
        ExportFormat.HTML: 'Web format - viewable in browsers',
        ExportFormat.MARKDOWN: 'Plain text with formatting - version control friendly',
        ExportFormat.JSON: 'Structured data format - for integrations',
        ExportFormat.CSV: 'Spreadsheet format - for data analysis',
    }
    return descriptions.get(fmt, 'Unknown format')


def _get_format_support(fmt: ExportFormat) -> dict:
    return {
        'proposal': fmt in [ExportFormat.PDF, ExportFormat.DOCX, ExportFormat.HTML, ExportFormat.MARKDOWN, ExportFormat.JSON],
        'checklist': fmt in [ExportFormat.PDF, ExportFormat.DOCX, ExportFormat.HTML, ExportFormat.MARKDOWN, ExportFormat.JSON, ExportFormat.CSV],
        'risk_analysis': fmt in [ExportFormat.PDF, ExportFormat.DOCX, ExportFormat.HTML, ExportFormat.MARKDOWN, ExportFormat.JSON, ExportFormat.CSV],
    }


@router.get('/watermarks/presets')
async def get_watermark_presets():
    return {
        'presets': [
            {
                'id': 'confidential',
                'name': 'Confidential',
                'watermark': {
                    'text': 'CONFIDENTIAL',
                    'opacity': 0.15,
                    'font_size': 36,
                    'color': '#c53030',
                    'position': 'diagonal',
                    'diagonal_angle': 45,
                },
            },
            {
                'id': 'draft',
                'name': 'Draft',
                'watermark': {
                    'text': 'DRAFT',
                    'opacity': 0.10,
                    'font_size': 30,
                    'color': '#718096',
                    'position': 'diagonal',
                    'diagonal_angle': 45,
                },
            },
            {
                'id': 'internal',
                'name': 'Internal Use Only',
                'watermark': {
                    'text': 'INTERNAL USE ONLY',
                    'opacity': 0.12,
                    'font_size': 24,
                    'color': '#2c5282',
                    'position': 'tile',
                    'diagonal_angle': 30,
                },
            },
            {
                'id': 'review',
                'name': 'For Review',
                'watermark': {
                    'text': 'FOR REVIEW',
                    'opacity': 0.10,
                    'font_size': 28,
                    'color': '#805ad5',
                    'position': 'center',
                },
            },
        ]
    }


export_router = router