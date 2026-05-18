"""Compliance Checklist API Router"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ...core.checklist import (
    ChecklistEngine,
    ChecklistExportConfig,
    ChecklistExportFormat,
    CompleteChecklist,
    ChecklistGenerationRequest,
    ChecklistGenerationResponse,
    ChecklistUpdateRequest,
    get_checklist_engine,
    DocumentStatus,
)


router = APIRouter(prefix='/checklist', tags=['compliance_checklist'])


class GenerateChecklistRequest(BaseModel):
    document_id: UUID
    document_text: str = Field(..., min_length=100)
    tender_id: Optional[UUID] = None
    include_optional_items: bool = True


class UpdateItemRequest(BaseModel):
    item_id: str
    status: Optional[str] = None
    is_submitted: Optional[bool] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ExportRequest(BaseModel):
    format: str = Field(default='json', description='pdf, excel, csv, json, html, markdown')
    include_completed: bool = True
    include_pending: bool = True
    include_optional: bool = False


@router.post('/generate', response_model=ChecklistGenerationResponse)
async def generate_checklist(
    request: GenerateChecklistRequest,
    engine: ChecklistEngine = Depends(get_checklist_engine),
):
    try:
        gen_request = ChecklistGenerationRequest(
            document_id=request.document_id,
            document_text=request.document_text,
            tender_id=request.tender_id,
        )
        return await engine.generate(gen_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{checklist_id}')
async def get_checklist(checklist_id: str):
    return {'checklist_id': checklist_id, 'status': 'pending', 'message': 'Use POST to generate'}


@router.get('/{checklist_id}/full')
async def get_full_checklist(
    checklist_id: str,
    document_text: str,
    document_id: Optional[UUID] = None,
    engine: ChecklistEngine = Depends(get_checklist_engine),
):
    try:
        checklist = await engine.get_full_checklist(document_text, document_id)
        return checklist.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/{checklist_id}/item')
async def update_item(
    checklist_id: str,
    request: UpdateItemRequest,
):
    return {'item_id': request.item_id, 'updated': True}


@router.get('/{checklist_id}/missing-items')
async def get_missing_items(checklist_id: str):
    return {'checklist_id': checklist_id, 'missing_items': []}


@router.post('/{checklist_id}/export')
async def export_checklist(
    checklist_id: str,
    request: ExportRequest,
    document_text: Optional[str] = None,
    engine: ChecklistEngine = Depends(get_checklist_engine),
):
    try:
        if not document_text:
            return {'error': 'document_text required for export'}

        checklist = await engine.get_full_checklist(document_text)

        from ...core.checklist.service import ChecklistExporter
        exporter = ChecklistExporter(checklist)

        format_map = {
            'json': ('application/json', exporter.to_json),
            'csv': ('text/csv', exporter.to_csv),
            'markdown': ('text/markdown', exporter.to_markdown),
            'html': ('text/html', exporter.to_html),
        }

        if request.format not in format_map:
            return {'error': f'Unsupported format: {request.format}. Use: json, csv, markdown, html'}

        content_type, content_func = format_map[request.format]
        content = content_func()

        return Response(content=content.encode(), media_type=content_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{checklist_id}/progress')
async def get_progress(checklist_id: str):
    return {
        'checklist_id': checklist_id,
        'completion_percentage': 0,
        'total_items': 0,
        'completed_items': 0,
        'pending_items': 0,
        'score': 0,
    }


@router.get('/{checklist_id}/sections')
async def get_sections(checklist_id: str):
    return {'checklist_id': checklist_id, 'sections': []}


@router.get('/{checklist_id}/steps')
async def get_submission_steps(checklist_id: str):
    return {'checklist_id': checklist_id, 'steps': []}


@router.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'checklist'}