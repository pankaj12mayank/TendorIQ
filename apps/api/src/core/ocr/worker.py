"""OCR background job handler (in-process)."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import Document, OCRResult as OCRResultModel, Tenant
from ...core.storage import storage_service
from ...core.logging import get_logger

logger = get_logger('ocr_worker')

OCR_MAX_RETRIES = 3
OCR_RETRY_DELAY_SECONDS = 60


async def process_ocr_job(ctx: dict) -> dict:
    from .paddle_ocr import paddle_ocr_service

    db: AsyncSession = ctx['db']
    document_id: str = ctx['document_id']
    tenant_id: str = ctx['tenant_id']
    retry_count: int = ctx.get('retry_count', 0)

    logger.info(f'Processing OCR job for document {document_id}', retry=retry_count)

    doc = await db.execute(
        select(Document).where(Document.id == UUID(document_id))
    )
    document = doc.scalar_one_or_none()

    if not document:
        return {'success': False, 'error': 'Document not found'}

    try:
        await db.execute(
            update(Document)
            .where(Document.id == UUID(document_id))
            .values(processing_status='processing')
        )
        await db.commit()

        storage_key = document.storage_key

        if storage_service.is_local:
            read_result = await storage_service.read_file(storage_key)
            if not read_result.get('success'):
                raise Exception(f'Failed to read file: {read_result.get("error")}')
            file_bytes = read_result['content']
        else:
            signed_url_result = await storage_service.generate_signed_download_url(
                storage_key=storage_key,
                expires_seconds=3600,
            )

            if not signed_url_result.get('success'):
                raise Exception(f'Failed to get download URL: {signed_url_result.get("error")}')

            import httpx
            file_response = httpx.get(signed_url_result['download_url'], timeout=60.0)
            file_response.raise_for_status()
            file_bytes = file_response.content

        is_pdf = document.file_type.lower() in ('pdf', 'pdf/a')

        quality_estimate = paddle_ocr_service.estimate_quality(file_bytes)

        if quality_estimate['needs_enhancement']:
            logger.info(f'Document {document_id} needs enhancement', quality=quality_estimate)

        if is_pdf:
            ocr_results = paddle_ocr_service.process_pdf(
                pdf_bytes=file_bytes,
                language='en',
                min_confidence=0.5,
            )
            combined_text = '\n\n'.join([r.text for r in ocr_results])
            avg_confidence = sum(r.confidence for r in ocr_results) / len(ocr_results) if ocr_results else 0
            is_low_quality = any(r.is_low_quality for r in ocr_results)
            word_count = sum(r.word_count for r in ocr_results)
        else:
            result = paddle_ocr_service.process_image(
                image_bytes=file_bytes,
                language='en',
                min_confidence=0.5,
            )
            combined_text = result.text
            avg_confidence = result.confidence
            is_low_quality = result.is_low_quality
            word_count = result.word_count

        ocr_record = OCRResultModel(
            document_id=UUID(document_id),
            tenant_id=UUID(tenant_id),
            extracted_text=combined_text,
            confidence_score=float(avg_confidence),
            word_count=word_count,
            language='en',
            is_low_quality=is_low_quality,
            blur_score=quality_estimate.get('blur_score'),
            brightness_score=quality_estimate.get('brightness_score'),
            contrast_score=quality_estimate.get('contrast_score'),
            overall_quality_score=quality_estimate.get('overall_quality'),
            processing_time_ms=0,
            status='completed',
            completed_at=datetime.now(timezone.utc),
            metadata={
                'retry_count': retry_count,
                'quality_estimate': quality_estimate,
                'is_pdf': is_pdf,
            },
        )
        db.add(ocr_record)

        new_status = 'needs_review' if is_low_quality else 'completed'

        await db.execute(
            update(Document)
            .where(Document.id == UUID(document_id))
            .values(
                processing_status=new_status,
                metadata={
                    **(document.metadata_json or {}),
                    'ocr_completed': True,
                    'ocr_confidence': avg_confidence,
                    'ocr_word_count': word_count,
                },
            )
        )
        await db.commit()

        logger.info(f'OCR completed for document {document_id}', status=new_status, confidence=avg_confidence)

        return {
            'success': True,
            'document_id': document_id,
            'status': new_status,
            'confidence': avg_confidence,
            'word_count': word_count,
            'is_low_quality': is_low_quality,
        }

    except Exception as e:
        logger.error(f'OCR job failed for document {document_id}: {e}', exc_info=True)

        retry_count += 1

        if retry_count < OCR_MAX_RETRIES:
            await db.execute(
                update(Document)
                .where(Document.id == UUID(document_id))
                .values(processing_status='retrying')
            )
            await db.commit()

            return {
                'success': False,
                'error': str(e),
                'retry_count': retry_count,
                'should_retry': True,
            }

        await db.execute(
            update(Document)
            .where(Document.id == UUID(document_id))
            .values(
                processing_status='failed',
                metadata={
                    **(document.metadata_json or {}),
                    'ocr_error': str(e),
                    'ocr_failed_at': datetime.now(timezone.utc).isoformat(),
                },
            )
        )

        ocr_record = OCRResultModel(
            document_id=UUID(document_id),
            tenant_id=UUID(tenant_id),
            extracted_text='',
            confidence_score=0,
            word_count=0,
            language='en',
            is_low_quality=False,
            status='failed',
            error_message=str(e),
            processing_time_ms=0,
            retry_count=retry_count,
        )
        db.add(ocr_record)
        await db.commit()

        return {
            'success': False,
            'error': str(e),
            'retry_count': retry_count,
            'should_retry': False,
        }


async def queue_ocr_job(
    db: AsyncSession,
    document_id: str,
    tenant_id: str,
    retry_count: int = 0,
) -> str:
    from ..tasks.inline import schedule_job

    job_id = schedule_job(
        'process_ocr_job',
        document_id=document_id,
        tenant_id=str(tenant_id),
        retry_count=retry_count,
    )
    logger.info('Scheduled in-process OCR job %s for document %s', job_id, document_id)
    return job_id