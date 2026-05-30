"""Document Service - Full Document Management"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import Document, Tenant
from ...core.logging import get_logger

logger = get_logger('document_service')


class DocumentService:
    @staticmethod
    async def create_document(
        db: AsyncSession,
        tenant_id: UUID,
        name: str,
        file_name: str,
        file_type: str,
        file_size: int,
        storage_key: str,
        storage_provider: str = 's3',
        mime_type: Optional[str] = None,
        checksum: Optional[str] = None,
        tender_id: Optional[UUID] = None,
        folder: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
        created_by_id: Optional[UUID] = None,
    ) -> Document:
        meta = dict(metadata or {})
        if created_by_id:
            meta.setdefault('uploaded_by_id', str(created_by_id))
        doc = Document(
            tenant_id=tenant_id,
            name=name,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            storage_key=storage_key,
            storage_provider=storage_provider,
            mime_type=mime_type,
            checksum=checksum,
            tender_id=tender_id,
            folder=folder,
            tags=tags or [],
            metadata_json=meta,
            processing_status='uploaded',
            uploaded_at=datetime.now(timezone.utc),
        )
        db.add(doc)
        await db.flush()
        await db.refresh(doc)
        logger.info(f'Document created: {doc.id}', tenant_id=str(tenant_id), file_name=file_name)
        return doc

    @staticmethod
    async def get_document(db: AsyncSession, document_id: UUID, tenant_id: UUID) -> Optional[Document]:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        tenant_id: UUID,
        owner_id: Optional[UUID] = None,
        search: Optional[str] = None,
        statuses: Optional[list[str]] = None,
        file_types: Optional[list[str]] = None,
        tender_id: Optional[UUID] = None,
        folder: Optional[str] = None,
        tags: Optional[list[str]] = None,
        is_archived: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Document], int]:
        query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
            Document.is_archived == is_archived,
        )
        if owner_id:
            query = query.where(Document.owner_id == owner_id)

        if search:
            search_term = f'%{search}%'
            query = query.where(
                or_(
                    Document.name.ilike(search_term),
                    Document.file_name.ilike(search_term),
                )
            )

        if statuses:
            query = query.where(Document.processing_status.in_(statuses))

        if file_types:
            query = query.where(Document.file_type.in_(file_types))

        if tender_id:
            query = query.where(Document.tender_id == tender_id)

        if folder:
            query = query.where(Document.folder == folder)

        if tags:
            for tag in tags:
                query = query.where(Document.tags.contains([tag]))

        if date_from:
            query = query.where(Document.created_at >= date_from)

        if date_to:
            query = query.where(Document.created_at <= date_to)

        order_col = getattr(Document, sort_by, Document.created_at)
        if sort_order == 'asc':
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * limit).limit(limit)

        result = await db.execute(query)
        documents = result.scalars().all()

        return list(documents), total

    @staticmethod
    async def update_document(
        db: AsyncSession,
        document_id: UUID,
        tenant_id: UUID,
        **updates,
    ) -> Optional[Document]:
        doc = await DocumentService.get_document(db, document_id, tenant_id)
        if not doc:
            return None

        for key, value in updates.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        await db.flush()
        await db.refresh(doc)
        logger.info(f'Document updated: {document_id}')
        return doc

    @staticmethod
    async def update_processing_status(
        db: AsyncSession,
        document_id: UUID,
        tenant_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[Document]:
        doc = await DocumentService.get_document(db, document_id, tenant_id)
        if not doc:
            return None

        doc.processing_status = status

        if error_message:
            doc.processing_error = error_message

        if status == 'completed':
            doc.processed_at = datetime.now(timezone.utc)

        if metadata:
            doc.metadata_json = {**(doc.metadata_json or {}), **metadata}

        await db.flush()
        await db.refresh(doc)
        logger.info(f'Document status updated: {document_id} -> {status}')
        return doc

    @staticmethod
    async def retry_document(
        db: AsyncSession,
        document_id: UUID,
        tenant_id: UUID,
    ) -> Optional[Document]:
        doc = await DocumentService.get_document(db, document_id, tenant_id)
        if not doc:
            return None

        if doc.retry_count >= doc.max_retries:
            logger.warning(f'Document max retries exceeded: {document_id}')
            return None

        doc.processing_status = 'retrying'
        doc.retry_count += 1
        doc.processing_error = None

        await db.flush()
        await db.refresh(doc)
        logger.info(f'Document retry initiated: {document_id}, attempt {doc.retry_count}')
        return doc

    @staticmethod
    async def soft_delete_document(
        db: AsyncSession,
        document_id: UUID,
        tenant_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        doc = await DocumentService.get_document(db, document_id, tenant_id)
        if not doc:
            return False

        doc.deleted_at = datetime.now(timezone.utc)
        doc.deleted_by_id = deleted_by_id
        doc.processing_status = 'deleted'
        await db.flush()
        logger.info(f'Document soft-deleted: {document_id}')
        return True

    @staticmethod
    async def permanent_delete_document(
        db: AsyncSession,
        document_id: UUID,
        tenant_id: UUID,
    ) -> Optional[Document]:
        doc = await DocumentService.get_document(db, document_id, tenant_id)
        if not doc:
            return None

        await db.delete(doc)
        await db.flush()
        logger.info(f'Document permanently deleted: {document_id}')
        return doc

    @staticmethod
    async def archive_documents(
        db: AsyncSession,
        document_ids: list[UUID],
        tenant_id: UUID,
    ) -> int:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(Document)
            .where(
                Document.id.in_(document_ids),
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
            .values(is_archived=True, archived_at=now)
        )
        await db.flush()
        logger.info(f'Documents archived: {result.rowcount}')
        return result.rowcount

    @staticmethod
    async def unarchive_documents(
        db: AsyncSession,
        document_ids: list[UUID],
        tenant_id: UUID,
    ) -> int:
        result = await db.execute(
            update(Document)
            .where(
                Document.id.in_(document_ids),
                Document.tenant_id == tenant_id,
                Document.is_archived == True,
            )
            .values(is_archived=False, archived_at=None)
        )
        await db.flush()
        logger.info(f'Documents unarchived: {result.rowcount}')
        return result.rowcount

    @staticmethod
    async def batch_delete(
        db: AsyncSession,
        document_ids: list[UUID],
        tenant_id: UUID,
        permanently: bool = False,
    ) -> tuple[int, int]:
        success = 0
        failed = 0

        for doc_id in document_ids:
            doc = await DocumentService.get_document(db, doc_id, tenant_id)
            if not doc:
                failed += 1
                continue

            if permanently:
                await db.delete(doc)
            else:
                doc.deleted_at = datetime.now(timezone.utc)
                doc.processing_status = 'deleted'

            success += 1

        await db.flush()
        return success, failed

    @staticmethod
    async def get_document_stats(
        db: AsyncSession,
        tenant_id: UUID,
        owner_id: Optional[UUID] = None,
    ) -> dict:
        base_query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
            Document.is_archived == False,
        )
        if owner_id:
            base_query = base_query.where(Document.owner_id == owner_id)

        result = await db.execute(base_query)
        docs = result.scalars().all()

        total_files = len(docs)
        total_size = sum(doc.file_size or 0 for doc in docs)

        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}

        for doc in docs:
            status = doc.processing_status or 'unknown'
            by_status[status] = by_status.get(status, 0) + 1

            file_type = doc.file_type or 'unknown'
            by_type[file_type] = by_type.get(file_type, 0) + 1

        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()

        quota_storage_mb = tenant.quota_storage_mb if tenant else 1024
        storage_usage_percent = (total_size / (quota_storage_mb * 1024 * 1024) * 100) if total_size > 0 else 0

        return {
            'total_documents': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_status': by_status,
            'by_type': by_type,
            'failed_count': by_status.get('failed', 0),
            'needs_review_count': by_status.get('needs_review', 0),
            'pending_count': by_status.get('uploaded', 0) + by_status.get('processing', 0) + by_status.get('retrying', 0),
            'quota_usage_percent': round(storage_usage_percent, 2),
        }

    @staticmethod
    async def check_quota(
        db: AsyncSession,
        tenant_id: UUID,
        file_size: int,
        file_count_add: int = 1,
    ) -> dict:
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()

        if not tenant:
            return {
                'allowed': False,
                'current_storage_mb': 0,
                'current_files': 0,
                'quota_storage_mb': 0,
                'quota_files': 0,
                'storage_remaining_mb': 0,
                'files_remaining': 0,
                'upgrade_required': True,
            }

        current_storage_mb = (tenant.used_storage_mb or 0)
        current_files = (tenant.used_documents or 0)
        quota_storage_mb = tenant.quota_storage_mb or 1024
        quota_files = tenant.quota_documents or 100

        file_size_mb = file_size / (1024 * 1024)
        new_storage_mb = current_storage_mb + file_size_mb
        new_files = current_files + file_count_add

        storage_ok = new_storage_mb <= quota_storage_mb
        files_ok = new_files <= quota_files

        return {
            'allowed': storage_ok and files_ok,
            'current_storage_mb': round(current_storage_mb, 2),
            'current_files': current_files,
            'quota_storage_mb': quota_storage_mb,
            'quota_files': quota_files,
            'storage_remaining_mb': round(max(0, quota_storage_mb - current_storage_mb), 2),
            'files_remaining': max(0, quota_files - current_files),
            'upgrade_required': not (storage_ok and files_ok),
        }

    @staticmethod
    async def update_quota_usage(
        db: AsyncSession,
        tenant_id: UUID,
        file_size: int,
        increment: bool = True,
    ) -> None:
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()

        if not tenant:
            return

        file_size_mb = file_size / (1024 * 1024)

        if increment:
            tenant.used_storage_mb = (tenant.used_storage_mb or 0) + file_size_mb
        else:
            tenant.used_storage_mb = max(0, (tenant.used_storage_mb or 0) - file_size_mb)

        await db.flush()


document_service = DocumentService()