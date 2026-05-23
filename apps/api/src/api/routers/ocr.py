"""OCR API Router"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.rbac_deps import (
    RequireDocumentCreate,
    RequireDocumentRead,
    require_tenant_member,
)
from ..services.document_service import document_service
from ...core.config import settings
from ...core.storage import storage_service
from ...core.ocr.paddle_ocr import paddle_ocr_service
from ...core.logging import get_logger
from ..schemas.ocr import (
    OCRJobCreate,
    OCRJobResponse,
    OCRResultResponse,
    OCRStatusResponse,
    OCRRetryRequest,
    OCRRetryResponse,
    QualityAssessmentResponse,
)
from ...core.database import get_db

router = APIRouter(
    prefix='/ocr',
    tags=['ocr'],
    dependencies=[Depends(require_tenant_member)],
)
logger = get_logger('ocr_api')


async def require_document_ocr_enabled() -> None:
    if not settings.FEATURE_DOCUMENT_OCR:
        raise HTTPException(status_code=403, detail='Document OCR is disabled')


@router.post('/process/{document_id}', dependencies=[Depends(require_document_ocr_enabled)])
async def process_document_ocr(
    document_id: str,
    current_user: RequireDocumentCreate,
    db: AsyncSession = Depends(get_db),
    language: str = Query('en', max_length=10),
    priority: int = Query(0, ge=0, le=10),
    body: Optional[dict] = Body(None),
):
    """Trigger OCR processing for a document"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    if body and body.get('language'):
        language = str(body['language'])[:10]

    doc = await document_service.get_document(
        db, UUID(document_id), UUID(current_user.tenant_id)
    )
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if doc.processing_status not in ('uploaded', 'failed', 'needs_review'):
        raise HTTPException(
            status_code=400,
            detail=f'Cannot process document with status: {doc.processing_status}',
        )

    from ...core.ocr.worker import queue_ocr_job

    await document_service.update_document(
        db, UUID(document_id), UUID(current_user.tenant_id),
        processing_status='processing',
    )

    try:
        job_id = await queue_ocr_job(
            db=db,
            document_id=document_id,
            tenant_id=current_user.tenant_id,
        )

        return {
            'success': True,
            'job_id': job_id,
            'document_id': document_id,
            'status': 'queued',
            'queued_at': datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f'Failed to queue OCR job: {e}')
        await document_service.update_document(
            db, UUID(document_id), UUID(current_user.tenant_id),
            processing_status='failed',
        )
        raise HTTPException(status_code=500, detail='Failed to queue OCR job')


@router.get('/status/{document_id}', response_model=OCRStatusResponse, dependencies=[Depends(require_document_ocr_enabled)])
async def get_ocr_status(
    document_id: str,
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
):
    """Get OCR status for a document"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.get_document(
        db, UUID(document_id), UUID(current_user.tenant_id)
    )
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    from sqlalchemy import select
    from ...core.models import OCRResult, OCRJob

    ocr_result = None
    ocr_job = None

    result_row = await db.execute(
        select(OCRResult)
        .where(
            OCRResult.document_id == UUID(document_id),
            OCRResult.tenant_id == UUID(current_user.tenant_id),
        )
        .order_by(OCRResult.created_at.desc())
    )
    ocr_result_row = result_row.scalar_one_or_none()

    job_row = await db.execute(
        select(OCRJob)
        .where(
            OCRJob.document_id == UUID(document_id),
            OCRJob.tenant_id == UUID(current_user.tenant_id),
        )
        .order_by(OCRJob.created_at.desc())
    )
    ocr_job_row = job_row.scalar_one_or_none()

    result_data = None
    job_data = None

    if ocr_result_row:
        result_data = OCRResultResponse(
            id=str(ocr_result_row.id),
            document_id=str(ocr_result_row.document_id),
            tenant_id=str(ocr_result_row.tenant_id),
            extracted_text=ocr_result_row.extracted_text,
            confidence_score=ocr_result_row.confidence_score,
            word_count=ocr_result_row.word_count,
            language=ocr_result_row.language,
            is_low_quality=ocr_result_row.is_low_quality,
            blur_score=ocr_result_row.blur_score,
            brightness_score=ocr_result_row.brightness_score,
            contrast_score=ocr_result_row.contrast_score,
            overall_quality_score=ocr_result_row.overall_quality_score,
            processing_time_ms=ocr_result_row.processing_time_ms,
            status=ocr_result_row.status,
            error_message=ocr_result_row.error_message,
            retry_count=ocr_result_row.retry_count,
            metadata=ocr_result_row.metadata_json or {},
            started_at=ocr_result_row.started_at,
            completed_at=ocr_result_row.completed_at,
            created_at=ocr_result_row.created_at,
            updated_at=ocr_result_row.updated_at,
        )

    if ocr_job_row:
        job_data = OCRJobResponse(
            id=str(ocr_job_row.id),
            document_id=str(ocr_job_row.document_id),
            tenant_id=str(ocr_job_row.tenant_id),
            arq_job_id=ocr_job_row.arq_job_id,
            status=ocr_job_row.status,
            priority=ocr_job_row.priority,
            retry_count=ocr_job_row.retry_count,
            max_retries=ocr_job_row.max_retries,
            error_message=ocr_job_row.error_message,
            result_summary=ocr_job_row.result_summary or {},
            started_at=ocr_job_row.started_at,
            completed_at=ocr_job_row.completed_at,
            created_at=ocr_job_row.created_at,
            updated_at=ocr_job_row.updated_at,
        )

    return OCRStatusResponse(
        success=True,
        document_id=document_id,
        ocr_status=doc.processing_status,
        has_result=ocr_result_row is not None,
        result=result_data,
        job=job_data,
    )


@router.get('/result/{document_id}', dependencies=[Depends(require_document_ocr_enabled)])
async def get_ocr_result(
    document_id: str,
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
):
    """Get OCR result text for a document"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    from sqlalchemy import select
    from ...core.models import OCRResult

    result = await db.execute(
        select(OCRResult)
        .where(
            OCRResult.document_id == UUID(document_id),
            OCRResult.tenant_id == UUID(current_user.tenant_id),
        )
        .order_by(OCRResult.created_at.desc())
    )
    ocr_result = result.scalar_one_or_none()

    if not ocr_result:
        raise HTTPException(status_code=404, detail='OCR result not found')

    return {
        'success': True,
        'result': {
            'id': str(ocr_result.id),
            'text': ocr_result.extracted_text,
            'confidence': ocr_result.confidence_score,
            'word_count': ocr_result.word_count,
            'language': ocr_result.language,
            'is_low_quality': ocr_result.is_low_quality,
            'quality_scores': {
                'blur': ocr_result.blur_score,
                'brightness': ocr_result.brightness_score,
                'contrast': ocr_result.contrast_score,
                'overall': ocr_result.overall_quality_score,
            },
            'status': ocr_result.status,
            'completed_at': ocr_result.completed_at.isoformat() if ocr_result.completed_at else None,
        },
    }


@router.post('/retry', response_model=OCRRetryResponse, dependencies=[Depends(require_document_ocr_enabled)])
async def retry_ocr(
    data: OCRRetryRequest,
    current_user: RequireDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Retry OCR for failed documents"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    from ...core.ocr.worker import queue_ocr_job

    retried = 0
    skipped = 0
    errors = []

    for doc_id in data.document_ids:
        try:
            doc = await document_service.get_document(
                db, UUID(doc_id), UUID(current_user.tenant_id)
            )
            if not doc:
                skipped += 1
                errors.append(f'Document {doc_id}: not found')
                continue

            if doc.processing_status == 'completed':
                skipped += 1
                errors.append(f'Document {doc_id}: already completed')
                continue

            await document_service.update_document(
                db, UUID(doc_id), UUID(current_user.tenant_id),
                processing_status='retrying',
            )

            await queue_ocr_job(
                db=db,
                document_id=doc_id,
                tenant_id=current_user.tenant_id,
                retry_count=0,
            )

            retried += 1

        except Exception as e:
            skipped += 1
            errors.append(f'Document {doc_id}: {str(e)}')

    return OCRRetryResponse(
        success=True,
        retried_count=retried,
        skipped_count=skipped,
        errors=errors,
    )


@router.get('/quality/{document_id}', response_model=QualityAssessmentResponse, dependencies=[Depends(require_document_ocr_enabled)])
async def assess_document_quality(
    document_id: str,
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
):
    """Assess document quality for OCR readiness"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.get_document(
        db, UUID(document_id), UUID(current_user.tenant_id)
    )
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    try:
        if storage_service.is_local:
            read_result = await storage_service.read_file(doc.storage_key)
            if not read_result.get('success'):
                raise HTTPException(status_code=500, detail='Failed to read file')
            file_bytes = read_result['content']
        else:
            signed_result = await storage_service.generate_signed_download_url(
                storage_key=doc.storage_key,
                expires_seconds=300,
            )

            if not signed_result.get('success'):
                raise HTTPException(status_code=500, detail='Failed to get file')

            import httpx
            response = httpx.get(signed_result['download_url'], timeout=30.0)
            response.raise_for_status()
            file_bytes = response.content

        quality = paddle_ocr_service.estimate_quality(file_bytes)

        overall = quality['overall_quality']
        if overall >= 0.8:
            accuracy = 'High'
        elif overall >= 0.6:
            accuracy = 'Medium'
        elif overall >= 0.4:
            accuracy = 'Low'
        else:
            accuracy = 'Very Low'

        dpi = 200 if quality['needs_enhancement'] else 150

        return QualityAssessmentResponse(
            success=True,
            document_id=document_id,
            blur_score=quality['blur_score'],
            brightness_score=quality['brightness_score'],
            contrast_score=quality['contrast_score'],
            overall_quality=quality['overall_quality'],
            is_blurry=quality['is_blurry'],
            is_too_dark=quality['is_too_dark'],
            is_too_bright=quality['is_too_bright'],
            needs_enhancement=quality['needs_enhancement'],
            recommended_dpi=dpi,
            estimated_ocr_accuracy=accuracy,
        )

    except Exception as e:
        logger.error(f'Quality assessment failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/batch-status', dependencies=[Depends(require_document_ocr_enabled)])
async def get_batch_ocr_status(
    current_user: RequireDocumentRead,
    document_ids: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get OCR status for multiple documents"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    from sqlalchemy import select
    from ...core.models import OCRResult

    ids = document_ids.split(',')
    results = {}

    for doc_id in ids:
        try:
            doc = await document_service.get_document(
                db, UUID(doc_id), UUID(current_user.tenant_id)
            )

            if not doc:
                results[doc_id] = {'status': 'not_found'}
                continue

            ocr_result = await db.execute(
                select(OCRResult)
                .where(
                    OCRResult.document_id == UUID(doc_id),
                    OCRResult.tenant_id == UUID(current_user.tenant_id),
                )
                .order_by(OCRResult.created_at.desc())
            )
            ocr = ocr_result.scalar_one_or_none()

            results[doc_id] = {
                'document_status': doc.processing_status,
                'has_ocr_result': ocr is not None,
                'confidence': ocr.confidence_score if ocr else None,
                'word_count': ocr.word_count if ocr else None,
                'is_low_quality': ocr.is_low_quality if ocr else None,
            }

        except Exception as e:
            results[doc_id] = {'error': str(e)}

    return {'success': True, 'results': results}
