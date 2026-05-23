"""Document Management API Router"""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.models import Document

from ..dependencies.rbac_deps import (
    RequireDocumentCreate,
    RequireDocumentDelete,
    RequireDocumentRead,
    require_tenant_member,
)
from ..dependencies.audit import tenant_audit
from ..services.document_service import document_service
from ..services.file_service import file_service
from ...core.storage import assert_tenant_storage_key, storage_service
from ...core.config import settings
from ...core.logging import get_logger
from ..schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    ProcessingStatusUpdate,
    DocumentResponse,
    DocumentListItem,
    DocumentListResponse,
    QuotaCheckRequest,
    QuotaCheckResponse,
    RetryRequest,
    RetryResponse,
    BatchStatusUpdate,
    BatchUpdateResponse,
    DocumentStats,
    DocumentStatsResponse,
)

router = APIRouter(
    prefix='/documents',
    tags=['documents'],
    dependencies=[Depends(require_tenant_member)],
)
logger = get_logger('documents_api')


def _doc_to_response(doc) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        tenant_id=str(doc.tenant_id),
        tender_id=str(doc.tender_id) if doc.tender_id else None,
        name=doc.name,
        file_name=doc.file_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        storage_key=doc.storage_key,
        storage_provider=doc.storage_provider,
        storage_path=doc.storage_path,
        mime_type=doc.mime_type,
        checksum=doc.checksum,
        processing_status=doc.processing_status,
        processing_error=doc.processing_error,
        retry_count=doc.retry_count,
        max_retries=doc.max_retries,
        metadata=doc.metadata_json or {},
        tags=doc.tags or [],
        folder=doc.folder,
        is_public=doc.is_public,
        is_archived=doc.is_archived,
        archived_at=doc.archived_at,
        expires_at=doc.expires_at,
        access_count=doc.access_count,
        last_accessed_at=doc.last_accessed_at,
        uploaded_at=doc.uploaded_at,
        processed_at=doc.processed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _doc_to_list_item(doc) -> DocumentListItem:
    return DocumentListItem(
        id=str(doc.id),
        name=doc.name,
        file_name=doc.file_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        processing_status=doc.processing_status,
        retry_count=doc.retry_count,
        folder=doc.folder,
        tags=doc.tags or [],
        is_archived=doc.is_archived,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post('/upload/initiate')
async def initiate_document_upload(
    data: DocumentCreate,
    current_user: RequireDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Initiate document upload"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    quota = await document_service.check_quota(
        db, UUID(current_user.tenant_id), data.file_size
    )
    if not quota['allowed']:
        raise HTTPException(
            status_code=402,
            detail=f'Quota exceeded. Storage: {quota["storage_remaining_mb"]}MB remaining. Files: {quota["files_remaining"]} remaining.',
        )

    is_valid, error_msg = storage_service.validate_file(
        filename=data.file_name,
        file_size=data.file_size,
        content_type=data.mime_type,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    safe_filename = storage_service.sanitize_filename(data.file_name)
    storage_key = storage_service.generate_storage_key(
        tenant_id=current_user.tenant_id,
        category=data.category,
        filename=safe_filename,
        tender_id=data.tender_id,
    )

    mime_type = data.mime_type or storage_service.get_mime_type(data.file_name)
    file_ext = re.sub(r'^\.', '', safe_filename.rsplit('.', 1)[-1]) if '.' in safe_filename else ''

    doc = await document_service.create_document(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        name=data.name,
        file_name=safe_filename,
        file_type=file_ext,
        file_size=data.file_size,
        storage_key=storage_key,
        storage_provider=settings.STORAGE_PROVIDER,
        mime_type=mime_type,
        checksum=data.checksum,
        tender_id=UUID(data.tender_id) if data.tender_id else None,
        folder=data.folder,
        tags=data.tags,
        metadata=data.metadata,
        created_by_id=UUID(current_user.user_id),
    )

    signed_result = await storage_service.generate_signed_upload_url(
        storage_key=storage_key,
        content_type=mime_type,
        expires_seconds=3600,
    )

    return {
        'success': True,
        'document_id': str(doc.id),
        'storage_key': storage_key,
        'upload_url': signed_result.get('upload_url'),
        'expires_at': signed_result.get('expires_at'),
        'processing_status': doc.processing_status,
    }


@router.post('/upload/complete/{document_id}')
async def complete_document_upload(
    document_id: str,
    current_user: RequireDocumentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Mark upload complete and trigger processing"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.get_document(db, UUID(document_id), UUID(current_user.tenant_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    meta = await storage_service.get_file_metadata(doc.storage_key)
    if not meta.get('success'):
        raise HTTPException(status_code=400, detail='File not found in storage')

    await document_service.update_document(
        db, UUID(document_id), UUID(current_user.tenant_id),
        file_size=meta.get('content_length', doc.file_size),
        checksum=meta.get('etag', doc.checksum),
    )

    await document_service.update_processing_status(
        db, UUID(document_id), UUID(current_user.tenant_id),
        status='processing',
        metadata={'uploaded_by': current_user.user_id},
    )

    await document_service.update_quota_usage(
        db, UUID(current_user.tenant_id), meta.get('content_length', doc.file_size), True
    )

    try:
        await tenant_audit.log_create(
            db,
            UUID(current_user.tenant_id),
            UUID(current_user.user_id),
            resource_type='document',
            resource_id=UUID(document_id),
            action_type='upload',
            resource_name=doc.name,
            values={'file_name': doc.file_name, 'file_size': doc.file_size},
            request=request,
        )
    except Exception as exc:
        logger.warning('document upload audit failed id=%s: %s', document_id, exc)

    return {
        'success': True,
        'document_id': document_id,
        'processing_status': 'processing',
        'verified': True,
    }


@router.get('/list', response_model=DocumentListResponse)
async def list_documents(
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None, max_length=200),
    status_filter: Optional[str] = Query(None, alias='status'),
    file_type: Optional[str] = Query(None),
    tender_id: Optional[str] = Query(None),
    folder: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    is_archived: bool = Query(False),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query('created_at'),
    sort_order: str = Query('desc'),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List documents with filtering and pagination"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    statuses = status_filter.split(',') if status_filter else None
    file_types = file_type.split(',') if file_type else None
    tag_list = tags.split(',') if tags else None

    docs, total = await document_service.get_documents(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        search=search,
        statuses=statuses,
        file_types=file_types,
        tender_id=UUID(tender_id) if tender_id else None,
        folder=folder,
        tags=tag_list,
        is_archived=is_archived,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return DocumentListResponse(
        success=True,
        documents=[_doc_to_list_item(doc) for doc in docs],
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get('/stats', response_model=DocumentStatsResponse)
async def get_document_stats(
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
):
    """Get document statistics"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    stats = await document_service.get_document_stats(
        db, UUID(current_user.tenant_id)
    )

    return DocumentStatsResponse(
        success=True,
        tenant_id=current_user.tenant_id,
        stats=DocumentStats(**stats),
    )


@router.get('/quota', response_model=QuotaCheckResponse)
async def check_quota(
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
    file_size: int = Query(..., ge=1),
):
    """Check upload quota"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    quota = await document_service.check_quota(
        db, UUID(current_user.tenant_id), file_size
    )

    return QuotaCheckResponse(**quota)


@router.get('/download/{document_id}')
async def download_document(
    document_id: str,
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
    expires_seconds: int = Query(3600, ge=60, le=86400),
):
    """Get signed download URL"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.get_document(db, UUID(document_id), UUID(current_user.tenant_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if doc.processing_status not in ('completed', 'needs_review'):
        raise HTTPException(
            status_code=400,
            detail=f'Cannot download document with status: {doc.processing_status}',
        )

    assert_tenant_storage_key(doc.storage_key, current_user.tenant_id)
    signed_result = await storage_service.generate_signed_download_url(
        storage_key=doc.storage_key,
        expires_seconds=expires_seconds,
        filename=doc.file_name,
    )

    if not signed_result.get('success'):
        raise HTTPException(status_code=500, detail='Failed to generate download URL')

    await document_service.update_document(
        db, UUID(document_id), UUID(current_user.tenant_id),
        access_count=doc.access_count + 1,
    )

    return {
        'success': True,
        'document_id': document_id,
        'download_url': signed_result['download_url'],
        'expires_at': signed_result['expires_at'],
        'expires_in': signed_result['expires_in'],
    }


@router.get('/folders/list')
async def list_folders(
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
):
    """List all folders for tenant"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    from sqlalchemy import distinct, select

    result = await db.execute(
        select(distinct(Document.folder))
        .where(
            Document.tenant_id == UUID(current_user.tenant_id),
            Document.deleted_at.is_(None),
            Document.folder.isnot(None),
        )
        .order_by(Document.folder)
    )

    folders = [f[0] for f in result.all() if f[0]]

    return {'success': True, 'folders': folders}


@router.get('/{document_id}')
async def get_document(
    document_id: str,
    current_user: RequireDocumentRead,
    db: AsyncSession = Depends(get_db),
):
    """Get single document details"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.get_document(db, UUID(document_id), UUID(current_user.tenant_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    return {'success': True, 'document': _doc_to_response(doc)}


@router.patch('/{document_id}')
async def update_document(
    document_id: str,
    data: DocumentUpdate,
    current_user: RequireDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update document metadata"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.update_document(
        db, UUID(document_id), UUID(current_user.tenant_id),
        name=data.name,
        folder=data.folder,
        tags=data.tags,
        is_public=data.is_public,
        metadata=data.metadata,
    )

    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    return {'success': True, 'document': _doc_to_response(doc)}


@router.patch('/{document_id}/status')
async def update_document_status(
    document_id: str,
    data: ProcessingStatusUpdate,
    current_user: RequireDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update document processing status"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.update_processing_status(
        db, UUID(document_id), UUID(current_user.tenant_id),
        status=data.status,
        error_message=data.error_message,
        metadata=data.metadata,
    )

    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    return {'success': True, 'document': _doc_to_response(doc)}


@router.post('/retry', response_model=RetryResponse)
async def retry_documents(
    data: RetryRequest,
    current_user: RequireDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Retry failed documents"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    retried = 0
    skipped = 0
    errors = []

    for doc_id in data.document_ids:
        try:
            doc = await document_service.retry_document(
                db, UUID(doc_id), UUID(current_user.tenant_id)
            )
            if doc:
                retried += 1
            else:
                skipped += 1
                errors.append(f'Document {doc_id}: max retries exceeded or not found')
        except Exception as e:
            skipped += 1
            errors.append(f'Document {doc_id}: {str(e)}')

    return RetryResponse(
        success=True,
        retried_count=retried,
        skipped_count=skipped,
        errors=errors,
    )


@router.post('/batch')
async def batch_update_documents(
    data: BatchStatusUpdate,
    current_user: RequireDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Batch update documents (archive, restore, delete)"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc_ids = [UUID(did) for did in data.document_ids]

    if data.status == 'archived':
        updated = await document_service.archive_documents(
            db, doc_ids, UUID(current_user.tenant_id)
        )
    elif data.status == 'restored':
        updated = await document_service.unarchive_documents(
            db, doc_ids, UUID(current_user.tenant_id)
        )
    elif data.status == 'deleted':
        updated, failed = await document_service.batch_delete(
            db, doc_ids, UUID(current_user.tenant_id), permanently=False
        )
        return BatchUpdateResponse(
            success=True,
            updated_count=updated,
            errors=[f'{failed} documents not found'] if failed else [],
        )
    else:
        raise HTTPException(status_code=400, detail='Invalid status')

    return BatchUpdateResponse(
        success=True,
        updated_count=updated,
        errors=[],
    )


@router.delete('/{document_id}')
async def delete_document(
    document_id: str,
    current_user: RequireDocumentDelete,
    request: Request,
    db: AsyncSession = Depends(get_db),
    permanently: bool = Query(False),
):
    """Delete a document"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await document_service.get_document(db, UUID(document_id), UUID(current_user.tenant_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    from ...core.row_access import can_modify_tenant_resource, resource_owner_id_from_metadata

    owner_id = resource_owner_id_from_metadata(getattr(doc, 'metadata_json', None))
    if not can_modify_tenant_resource(
        user_id=current_user.user_id,
        membership_role=current_user.membership_role,
        created_by_id=owner_id,
        platform_role=current_user.role,
    ):
        raise HTTPException(
            status_code=403,
            detail='You may only delete documents you uploaded',
        )

    file_size = doc.file_size
    storage_key = doc.storage_key

    if permanently:
        assert_tenant_storage_key(storage_key, current_user.tenant_id)
        await storage_service.delete_file(storage_key)
        await document_service.permanent_delete_document(
            db, UUID(document_id), UUID(current_user.tenant_id)
        )
        await document_service.update_quota_usage(
            db, UUID(current_user.tenant_id), file_size, False
        )
    else:
        await document_service.soft_delete_document(
            db, UUID(document_id), UUID(current_user.tenant_id),
            deleted_by_id=UUID(current_user.user_id)
        )

    try:
        await tenant_audit.log_delete(
            db,
            UUID(current_user.tenant_id),
            UUID(current_user.user_id),
            resource_type='document',
            resource_id=UUID(document_id),
            action_type='document',
            resource_name=doc.name,
            old_values={'file_name': doc.file_name, 'permanently': permanently},
            request=request,
        )
    except Exception as exc:
        logger.warning('document delete audit failed id=%s: %s', document_id, exc)

    return {
        'success': True,
        'document_id': document_id,
        'deleted': True,
        'permanently': permanently,
    }
