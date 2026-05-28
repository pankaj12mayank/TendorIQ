"""File Storage API Router"""

import re
import hashlib
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from urllib.parse import unquote
from sqlalchemy.ext.asyncio import AsyncSession
import io

from ...core.database import get_db

from ..dependencies.access import TenantUser, require_tenant_member
from ..services.file_service import file_service
from ...core.storage import assert_tenant_storage_key, storage_service
from ...core.storage.tokens import verify_storage_token
from ...core.config import settings
from ...core.logging import get_logger
from ...core.upload_policy import (
    LITE_ALLOWED_EXTENSIONS,
    LITE_MAX_FILE_SIZE_MB,
    LITE_MIME_BY_EXT,
)
from ..schemas.storage import (
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

# Tokenized blob access (no session — validated via HMAC query token)
public_storage_router = APIRouter(prefix='/files', tags=['files-storage'])


@public_storage_router.put('/blob/{storage_key:path}')
async def put_blob_with_token(
    storage_key: str,
    request: Request,
    token: str = Query(...),
):
    """Tokenized PUT for local storage (presign-compatible upload flow)."""
    key = unquote(storage_key)
    if not verify_storage_token(token, key, 'put'):
        raise HTTPException(status_code=401, detail='Invalid or expired upload token')
    body = await request.body()
    result = await storage_service.upload_file(file_content=body, storage_key=key)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Upload failed'))
    return {'success': True, 'storage_key': key}


@public_storage_router.get('/blob/{storage_key:path}')
async def get_blob_with_token(
    storage_key: str,
    token: str = Query(...),
    filename: Optional[str] = Query(None),
):
    """Tokenized GET for local storage downloads."""
    key = unquote(storage_key)
    if not verify_storage_token(token, key, 'get'):
        raise HTTPException(status_code=401, detail='Invalid or expired download token')
    if not storage_service.is_local:
        raise HTTPException(status_code=400, detail='Blob route is for local storage only')
    path = storage_service._local_path(key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(path, filename=filename or path.name)


router = APIRouter(
    prefix='/files',
    tags=['files'],
    dependencies=[Depends(require_tenant_member)],
)
logger = get_logger('files_api')

PDF_MAGIC = b'%PDF-'
ZIP_MAGIC = b'PK\x03\x04'
OLE_MAGIC = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


def _assert_magic_bytes(filename: str, content: bytes) -> None:
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    if ext == 'pdf' and not content.startswith(PDF_MAGIC):
        raise HTTPException(status_code=400, detail='Corrupted or invalid PDF file')
    if ext == 'docx' and not content.startswith(ZIP_MAGIC):
        raise HTTPException(status_code=400, detail='Corrupted or invalid DOCX file')
    if ext == 'doc' and not content.startswith(OLE_MAGIC):
        raise HTTPException(status_code=400, detail='Corrupted or invalid DOC file')


@router.get('/upload/config')
async def get_upload_config(
    current_user: TenantUser,
) -> dict:
    """Lite upload limits and flow hint for the web uploader."""
    provider = settings.STORAGE_PROVIDER
    use_presigned = provider in ('r2', 's3')
    return {
        'success': True,
        'provider': provider,
        'max_file_size_mb': settings.STORAGE_MAX_FILE_SIZE_MB,
        'max_file_size_bytes': settings.max_file_size_bytes,
        'allowed_extensions': settings.allowed_extensions,
        'mime_types': LITE_MIME_BY_EXT,
        'use_presigned': use_presigned,
        'bucket': settings.STORAGE_BUCKET if use_presigned else None,
    }


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
        metadata=doc.metadata_json or {},
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post('/upload/initiate', response_model=FileUploadResponse)
async def initiate_upload(
    data: FileUploadRequest,
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
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
        owner_id=current_user.user_id,
    )

    is_valid, error_msg = storage_service.validate_file(
        filename=data.file_name,
        file_size=data.file_size,
        content_type=data.content_type,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    from ...core.billing.lite_usage import enforce_quota, track_usage

    await enforce_quota(db, UUID(tenant_id), 'upload_document')

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
        owner_id=UUID(current_user.user_id),
    )

    signed_result = await storage_service.generate_signed_upload_url(
        storage_key=storage_key,
        content_type=mime_type,
        expires_seconds=3600,
    )

    if not signed_result.get('success'):
        raise HTTPException(status_code=500, detail='Failed to generate upload URL')

    await track_usage(
        db,
        tenant_id=UUID(tenant_id),
        user_id=UUID(current_user.user_id),
        action='upload_document',
        resource_type='document',
        resource_id=doc.id,
    )
    await db.commit()

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
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
    ai_provider: Optional[str] = Query(None, alias='provider'),
    ai_model: Optional[str] = Query(None, alias='model'),
):
    """Mark upload as complete and verify file exists"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    from ...core.lite_scope import user_owns_row

    if str(doc.tenant_id) != current_user.tenant_id and not user_owns_row(doc, current_user.user_id):
        raise HTTPException(status_code=403, detail='Access denied')

    meta = await storage_service.get_file_metadata(doc.storage_key)
    if not meta.get('success'):
        raise HTTPException(status_code=400, detail='File not found in storage')

    from ...core.security.upload_scan import assert_upload_clean

    read_result = await storage_service.read_file(doc.storage_key)
    if read_result.get('success') and read_result.get('content'):
        await assert_upload_clean(read_result['content'], doc.file_name)

    await file_service.update_document(
        db,
        UUID(document_id),
        file_size=meta.get('content_length', doc.file_size),
        checksum=meta.get('etag', doc.checksum),
    )

    from ..services.document_service import document_service as doc_svc

    await doc_svc.update_processing_status(
        db,
        UUID(document_id),
        UUID(current_user.tenant_id),
        status='processing',
        metadata={'uploaded_by': current_user.user_id},
    )

    from ...core.processing.tasks import schedule_document_analysis

    file_bytes = b''
    content_hash = None
    if read_result.get('success') and read_result.get('content'):
        file_bytes = read_result['content']
        _assert_magic_bytes(doc.file_name, file_bytes)
        content_hash = hashlib.sha256(file_bytes).hexdigest()
    if content_hash:
        dup = await file_service.find_duplicate_document(
            db,
            tenant_id=UUID(current_user.tenant_id),
            checksum=content_hash,
            file_name=doc.file_name,
            exclude_document_id=UUID(document_id),
        )
        if dup:
            await file_service.permanent_delete_document(db, UUID(document_id))
            await storage_service.delete_file(doc.storage_key)
            raise HTTPException(
                status_code=409,
                detail=f'Duplicate file already uploaded (document_id={dup.id})',
            )
        await file_service.update_document(
            db,
            UUID(document_id),
            checksum=content_hash,
        )

    await schedule_document_analysis(
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        owner_id=current_user.user_id,
        provider=ai_provider,
        model=ai_model,
        force=True,
    )

    return {
        'success': True,
        'document_id': document_id,
        'verified': True,
        'processing_status': 'processing',
        'analysis_queued': True,
    }


@router.post('/upload/direct')
async def direct_upload(
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    tender_id: Optional[str] = Query(None),
    category: str = Query('documents'),
    ai_provider: Optional[str] = Query(None, alias='provider'),
    ai_model: Optional[str] = Query(None, alias='model'),
):
    """Direct upload via multipart form (local storage only; R2/S3 use presigned flow)."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    if settings.STORAGE_PROVIDER in ('r2', 's3'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Cloud storage requires presigned upload. Use POST /files/upload/initiate.',
        )

    contents = await file.read()

    from ...core.security.upload_scan import assert_upload_clean

    await assert_upload_clean(contents, file.filename or 'upload')
    _assert_magic_bytes(file.filename or 'upload', contents)

    is_valid, error_msg = storage_service.validate_file(
        filename=file.filename or 'unknown',
        file_size=len(contents),
        content_type=file.content_type,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    checksum = hashlib.sha256(contents).hexdigest()
    dup = await file_service.find_duplicate_document(
        db,
        tenant_id=UUID(current_user.tenant_id),
        checksum=checksum,
        file_name=file.filename or None,
    )
    if dup:
        raise HTTPException(
            status_code=409,
            detail=f'Duplicate file already uploaded (document_id={dup.id})',
        )

    from ...core.billing.lite_usage import enforce_quota, track_usage

    await enforce_quota(db, UUID(current_user.tenant_id), 'upload_document')

    safe_filename = storage_service.sanitize_filename(file.filename or 'upload')
    storage_key = storage_service.generate_storage_key(
        tenant_id=current_user.tenant_id,
        category=category,
        filename=safe_filename,
        tender_id=tender_id,
        owner_id=current_user.user_id,
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
        checksum=checksum,
        tender_id=UUID(tender_id) if tender_id else None,
        owner_id=UUID(current_user.user_id),
    )

    from ..services.document_service import document_service as doc_svc

    await doc_svc.update_processing_status(
        db,
        doc.id,
        UUID(current_user.tenant_id),
        status='processing',
        metadata={'uploaded_by': current_user.user_id},
    )

    await track_usage(
        db,
        tenant_id=UUID(current_user.tenant_id),
        user_id=UUID(current_user.user_id),
        action='upload_document',
        resource_type='document',
        resource_id=doc.id,
    )

    from ...core.processing.tasks import schedule_document_analysis

    await schedule_document_analysis(
        document_id=str(doc.id),
        tenant_id=current_user.tenant_id,
        owner_id=current_user.user_id,
        provider=ai_provider,
        model=ai_model,
        force=True,
    )
    await db.commit()

    return {
        'success': True,
        'document_id': str(doc.id),
        'storage_key': storage_key,
        'file_size': len(contents),
        'checksum': result.get('checksum'),
        'processing_status': 'processing',
        'analysis_queued': True,
    }


@router.get('/download/{document_id}', response_model=FileDownloadResponse)
async def download_file(
    document_id: str,
    current_user: TenantUser,
    db,
    expires_seconds: int = Query(3600, ge=60, le=86400),
):
    """Get signed download URL for a file"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    from ...core.lite_scope import user_owns_row

    if str(doc.tenant_id) != current_user.tenant_id and not user_owns_row(doc, current_user.user_id):
        raise HTTPException(status_code=403, detail='Access denied')

    assert_tenant_storage_key(
        doc.storage_key, current_user.tenant_id, owner_id=current_user.user_id
    )
    signed_result = await storage_service.generate_signed_download_url(
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
    current_user: TenantUser,
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
        owner_id=None if current_user.is_super_admin() else UUID(current_user.user_id),
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
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    """Get file metadata"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    from ...core.lite_scope import user_owns_row

    if str(doc.tenant_id) != current_user.tenant_id and not user_owns_row(doc, current_user.user_id):
        raise HTTPException(status_code=403, detail='Access denied')

    return {'success': True, 'document': _doc_to_response(doc)}


@router.delete('/{document_id}', response_model=FileDeleteResponse)
async def delete_file(
    document_id: str,
    current_user: TenantUser,
    db,
    permanently: bool = Query(False),
):
    """Delete a file"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    from ...core.lite_scope import user_owns_row

    if str(doc.tenant_id) != current_user.tenant_id and not user_owns_row(doc, current_user.user_id):
        raise HTTPException(status_code=403, detail='Access denied')

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

    storage_deleted = False
    if permanently:
        assert_tenant_storage_key(
        doc.storage_key, current_user.tenant_id, owner_id=current_user.user_id
    )
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
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
):
    """Generate a signed URL for upload or download"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail='Tenant context required')

    doc = await file_service.get_document(db, UUID(data.document_id))
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    from ...core.lite_scope import user_owns_row

    if str(doc.tenant_id) != current_user.tenant_id and not user_owns_row(doc, current_user.user_id):
        raise HTTPException(status_code=403, detail='Access denied')

    expires = data.expires_seconds or settings.STORAGE_SIGNED_URL_EXPIRE_SECONDS

    assert_tenant_storage_key(
        doc.storage_key, current_user.tenant_id, owner_id=current_user.user_id
    )
    if data.url_type == 'download':
        result = await storage_service.generate_signed_download_url(
            storage_key=doc.storage_key,
            expires_seconds=expires,
            filename=doc.file_name,
        )
    else:
        result = await storage_service.generate_signed_upload_url(
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
    current_user: TenantUser,
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
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
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
    current_user: TenantUser,
    db: AsyncSession = Depends(get_db),
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