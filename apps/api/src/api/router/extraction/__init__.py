"""Structured Extraction API Router"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ....core.extraction import (
    ExtractionService,
    ExtractionRequest,
    ExtractionResponse,
    CompleteExtractionResult,
    get_extraction_service,
    get_extraction_pipeline,
)


router = APIRouter(prefix='/extraction', tags=['extraction'])


class ExtractRequest(BaseModel):
    document_id: UUID
    document_text: str = Field(..., min_length=10, description="Document text to extract from")
    extraction_type: str = Field(default="full", description="full, summary, quick")
    fields_to_extract: Optional[list[str]] = None
    validation_strict: bool = False
    retry_on_failure: bool = True


class QuickExtractRequest(BaseModel):
    document_text: str = Field(..., min_length=10)


class SingleFieldRequest(BaseModel):
    document_text: str
    field_type: str


class ExtractResponse(BaseModel):
    extraction_id: str
    status: str
    confidence: float
    processing_time_ms: int
    retry_count: int
    errors: list[str]
    result: Optional[dict] = None


@router.post('/', response_model=ExtractResponse)
async def extract(request: ExtractRequest, service: ExtractionService = Depends(get_extraction_service)):
    try:
        extraction_req = ExtractionRequest(
            document_id=request.document_id,
            extraction_type=request.extraction_type,
            fields_to_extract=request.fields_to_extract,
            validation_strict=request.validation_strict,
            retry_on_failure=request.retry_on_failure,
        )

        response = await service.extract(request.document_text, extraction_req)

        return ExtractResponse(
            extraction_id=response.extraction_id,
            status=response.status.value,
            confidence=response.confidence,
            processing_time_ms=response.processing_time_ms,
            retry_count=response.retry_count,
            errors=response.errors,
            result=response.result.model_dump() if response.result else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/quick')
async def quick_extract(request: QuickExtractRequest, service: ExtractionService = Depends(get_extraction_service)):
    try:
        result = await service.quick_extract(request.document_text)
        return {
            'extraction_id': result.extraction_id,
            'status': result.status.value,
            'result': result.model_dump(),
            'overall_confidence': result.overall_confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/field')
async def extract_single_field(request: SingleFieldRequest, service: ExtractionService = Depends(get_extraction_service)):
    try:
        result = await service.extract_single_field(request.field_type, request.document_text)
        return {
            'field_type': request.field_type,
            'data': result.get('data'),
            'confidence': result.get('confidence', 0),
            'warnings': result.get('warnings', []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/batch')
async def batch_extract(requests: list[ExtractRequest], service: ExtractionService = Depends(get_extraction_service)):
    try:
        from uuid import uuid4

        extraction_reqs = []
        for req in requests:
            extraction_reqs.append((
                req.document_text,
                ExtractionRequest(
                    document_id=req.document_id,
                    extraction_type=req.extraction_type,
                    fields_to_extract=req.fields_to_extract,
                )
            ))

        pipeline = get_extraction_pipeline()
        results = await pipeline.batch_extract(extraction_reqs)

        return {
            'total': len(requests),
            'results': [
                {
                    'extraction_id': r.extraction_id,
                    'status': r.status.value,
                    'confidence': r.confidence,
                    'errors': r.errors,
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/fields')
async def list_extraction_fields():
    from ....core.extraction.prompts import ExtractionConfig
    return {
        'fields': ExtractionConfig.EXTRACTION_ORDER,
        'critical_fields': ExtractionConfig.CRITICAL_EXTRACTIONS,
    }


@router.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'extraction'}