"""File Storage API Router"""

import re
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
import io

from .dependencies.auth import CurrentUser
from .services.file_service import file_service
from .services.tenant_service import tenant_service
from ...core.storage import storage_service
from ...core.config import settings
from ...core.logging import get_logger
from .schemas.storage import (
    FileUploadRequest,
    FileUploadResponse,
    FileDownloadResponse,
    DocumentResponse,
    FileListResponse,
    FileDeleteResponse,
    SignedUrlRequest,
    SignedUrlResponse,
    StorageStatsResponse,
    FileValidationResponse,
    FileValidationError,
)

router = APIRouter(prefix='/files', tags=['files'])
logger = get_logger('files_api')


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
        is_public=doc.is_public,
        expires_at=doc.expires_at,
        is_archived=doc.is_archived,
        access_count=doc.access_count,
        metadata=doc.metadata or {},
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post('/upload/initiate', response_model=FileUploadResponse)
async def initiate_upload(
    data: FileUploadRequest,
    current_user: CurrentUser,
    db,
):
    """Initiate a file upload - generates storage key and signed URL"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    tenant_id = current_user.tenant_id

    safe_filename = storage_service.sanitize_filename(data.file_name)
    storage_key = storage_service.generate_storage_key(
        tenant_id=tenant_id,
        category=data.category,
        filename=safe_filename,
        tender_id=data.tender_id,
    )

    is_valid, error_msg = storage_service.validate_file(
        filename=data.file_name,
        file_size=data.file_size,
        content_type=data.content_type,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    mime_type = data.content_type or storage_service.get_mime_type(data.file_name)
    file_ext = re.sub(r'^\.', '', safe_filename.rsplit('.', 1)[-1]) if '.' in safe_filename else ''

    doc = await file_service.create_document(
        db=db,
        tenant_id=UUID(tenant_id),
        name=data.file_name,
        file_name=safe_filename,
        file_type=file_ext,
        file_size=data.file_size,
        storage_key=storage_key,
        storage_provider=settings.STORAGE_PROVIDER,
        mime_type=mime_type,
        tender_id=UUID(data.tender_id) if data.tender_id else None,
        created_by_id=UUID(current_user.user_id),
    )

    signed_result = storage_service.generate_signed_upload_url(
        storage_key=storage_key,
        content_type=mime_type,
        expires_seconds=3600,
    )

    if not signed_result.get('success'):
        raise HTTPException(status_code=500, detail='Failed to generate upload URL')

    return FileUploadResponse(
        success=True,
        document_id=str(doc.id),
        storage_key=storage_key,
        upload_url=signed_result['upload_url'],
        expires_at=signed_result['expires_at'],
        expires_in=signed_result['expires_in'],
    )


@router.post('/upload/complete/{document_id}')
async def complete_upload(
    document_id: str,
    current_user: CurrentUser,
    db,
):
    """Mark upload as complete and verify file exists"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if str(doc.tenant_id) != current_user.tenant_id:
        raise HTTPException(status_code=403, detail='Access denied')

    meta = await storage_service.get_file_metadata(doc.storage_key)
    if not meta.get('success'):
        raise HTTPException(status_code=400, detail='File not found in storage')

    await file_service.update_document(
        db,
        UUID(document_id),
        file_size=meta.get('content_length', doc.file_size),
        checksum=meta.get('etag', doc.checksum),
    )

    return {'success': True, 'document_id': document_id, 'verified': True}


@router.post('/upload/direct')
async def direct_upload(
    current_user: CurrentUser,
    db,
    file: UploadFile = File(...),
    tender_id: Optional[str] = Query(None),
    category: str = Query('documents'),
):
    """Direct upload via multipart form"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    contents = await file.read()

    is_valid, error_msg = storage_service.validate_file(
        filename=file.filename or 'unknown',
        file_size=len(contents),
        content_type=file.content_type,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    safe_filename = storage_service.sanitize_filename(file.filename or 'upload')
    storage_key = storage_service.generate_storage_key(
        tenant_id=current_user.tenant_id,
        category=category,
        filename=safe_filename,
        tender_id=tender_id,
    )

    result = await storage_service.upload_file(
        file_content=contents,
        storage_key=storage_key,
        content_type=file.content_type,
        metadata={'uploaded_by': current_user.user_id},
    )

    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Upload failed'))

    file_ext = re.sub(r'^\.', '', safe_filename.rsplit('.', 1)[-1]) if '.' in safe_filename else ''

    doc = await file_service.create_document(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        name=file.filename or safe_filename,
        file_name=safe_filename,
        file_type=file_ext,
        file_size=len(contents),
        storage_key=storage_key,
        storage_provider=settings.STORAGE_PROVIDER,
        mime_type=file.content_type,
        checksum=result.get('checksum'),
        tender_id=UUID(tender_id) if tender_id else None,
        created_by_id=UUID(current_user.user_id),
    )

    return {
        'success': True,
        'document_id': str(doc.id),
        'storage_key': storage_key,
        'file_size': len(contents),
        'checksum': result.get('checksum'),
    }


@router.get('/download/{document_id}', response_model=FileDownloadResponse)
async def download_file(
    document_id: str,
    current_user: CurrentUser,
    db,
    expires_seconds: int = Query(3600, ge=60, le=86400),
):
    """Get signed download URL for a file"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if str(doc.tenant_id) != current_user.tenant_id:
        raise HTTPException(status_code=403, detail='Access denied')

    signed_result = storage_service.generate_signed_download_url(
        storage_key=doc.storage_key,
        expires_seconds=expires_seconds,
        filename=doc.file_name,
    )

    if not signed_result.get('success'):
        raise HTTPException(status_code=500, detail='Failed to generate download URL')

    await file_service.track_access(db, UUID(document_id))

    return FileDownloadResponse(
        success=True,
        document_id=document_id,
        download_url=signed_result['download_url'],
        expires_at=signed_result['expires_at'],
        expires_in=signed_result['expires_in'],
        file_name=doc.file_name,
        file_size=doc.file_size,
        content_type=doc.mime_type,
    )


@router.get('/list', response_model=FileListResponse)
async def list_files(
    current_user: CurrentUser,
    db,
    tender_id: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    archived: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
):
    """List files for the current tenant"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    docs, total = await file_service.list_documents(
        db=db,
        tenant_id=UUID(current_user.tenant_id),
        tender_id=UUID(tender_id) if tender_id else None,
        file_type=file_type,
        is_archived=archived,
        page=page,
        limit=limit,
        search=search,
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return FileListResponse(
        success=True,
        files=[_doc_to_response(doc) for doc in docs],
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get('/{document_id}')
async def get_file(
    document_id: str,
    current_user: CurrentUser,
    db,
):
    """Get file metadata"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if str(doc.tenant_id) != current_user.tenant_id:
        raise HTTPException(status_code=403, detail='Access denied')

    return {'success': True, 'document': _doc_to_response(doc)}


@router.delete('/{document_id}', response_model=FileDeleteResponse)
async def delete_file(
    document_id: str,
    current_user: CurrentUser,
    db,
    permanently: bool = Query(False),
):
    """Delete a file"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if str(doc.tenant_id) != current_user.tenant_id:
        raise HTTPException(status_code=403, detail='Access denied')

    storage_deleted = False
    if permanently:
        result = await storage_service.delete_file(doc.storage_key)
        storage_deleted = result.get('success', False)
        await file_service.permanent_delete_document(db, UUID(document_id))
    else:
        await file_service.soft_delete_document(
            db,
            UUID(document_id),
            deleted_by_id=UUID(current_user.user_id),
        )

    return FileDeleteResponse(
        success=True,
        document_id=document_id,
        deleted=True,
        storage_deleted=storage_deleted,
    )


@router.post('/signed-url', response_model=SignedUrlResponse)
async def generate_signed_url(
    data: SignedUrlRequest,
    current_user: CurrentUser,
    db,
):
    """Generate a signed URL for upload or download"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(data.document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if str(doc.tenant_id) != current_user.tenant_id:
        raise HTTPException(status_code=403, detail='Access denied')

    expires = data.expires_seconds or settings.STORAGE_SIGNED_URL_EXPIRE_SECONDS

    if data.url_type == 'download':
        result = storage_service.generate_signed_download_url(
            storage_key=doc.storage_key,
            expires_seconds=expires,
            filename=doc.file_name,
        )
    else:
        result = storage_service.generate_signed_upload_url(
            storage_key=doc.storage_key,
            content_type=doc.mime_type,
            expires_seconds=expires,
        )

    if not result.get('success'):
        raise HTTPException(status_code=500, detail='Failed to generate URL')

    return SignedUrlResponse(
        success=True,
        url=result.get('download_url') or result.get('upload_url') or '',
        storage_key=doc.storage_key,
        expires_at=result['expires_at'],
        expires_in=result['expires_in'],
        url_type=data.url_type,
    )


@router.post('/validate')
async def validate_file(
    current_user: CurrentUser,
    file_name: str = Query(...),
    file_size: int = Query(..., ge=1),
    content_type: Optional[str] = Query(None),
):
    """Validate file before upload"""
    is_valid, error_msg = storage_service.validate_file(
        filename=file_name,
        file_size=file_size,
        content_type=content_type,
    )

    errors = []
    if not is_valid:
        errors.append(FileValidationError(field='file', message=error_msg))

    return FileValidationResponse(valid=is_valid, errors=errors)


@router.get('/stats/storage')
async def get_storage_stats(
    current_user: CurrentUser,
    db,
):
    """Get storage usage statistics for tenant"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    stats = await file_service.get_storage_stats(db, UUID(current_user.tenant_id))

    return StorageStatsResponse(
        success=True,
        tenant_id=current_user.tenant_id,
        total_files=stats['total_files'],
        total_size_bytes=stats['total_size_bytes'],
        total_size_mb=stats['total_size_mb'],
        by_type=stats['by_type'],
        by_category={},
    )


@router.post('/batch-delete')
async def batch_delete_files(
    document_ids: list[str],
    current_user: CurrentUser,
    db,
    permanently: bool = Query(False),
):
    """Batch delete multiple files"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    uuids = [UUID(did) for did in document_ids]
    docs = []
    storage_keys = []

    for doc_id in uuids:
        doc = await file_service.get_document(db, doc_id)
        if doc and str(doc.tenant_id) == current_user.tenant_id:
            docs.append(doc)
            storage_keys.append(doc.storage_key)

    if permanently and storage_keys:
        await storage_service.delete_files_batch(storage_keys)

    success, fail = await file_service.batch_delete(db, uuids)

    return {
        'success': True,
        'deleted_count': success,
        'failed_count': fail,
        'errors': [],
    }