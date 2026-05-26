"""File Service - Database Operations for Documents"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import Document
from ...core.logging import get_logger

logger = get_logger('file_service')


class FileService:
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
        metadata: Optional[dict] = None,
        owner_id: Optional[UUID] = None,
    ) -> Document:
        doc = Document(
            tenant_id=tenant_id,
            owner_id=owner_id,
            name=name,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            storage_key=storage_key,
            storage_provider=storage_provider,
            mime_type=mime_type,
            checksum=checksum,
            tender_id=tender_id,
            metadata_json=metadata or {},
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        logger.info(f'Document created: {doc.id}', tenant_id=str(tenant_id), file_name=file_name)
        return doc

    @staticmethod
    async def get_document(db: AsyncSession, document_id: UUID) -> Optional[Document]:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_document_by_storage_key(
        db: AsyncSession,
        storage_key: str,
        tenant_id: UUID,
    ) -> Optional[Document]:
        result = await db.execute(
            select(Document).where(
                Document.storage_key == storage_key,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        tenant_id: UUID,
        tender_id: Optional[UUID] = None,
        file_type: Optional[str] = None,
        is_archived: bool = False,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
    ) -> tuple[list[Document], int]:
        query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
            Document.is_archived == is_archived,
        )

        if tender_id:
            query = query.where(Document.tender_id == tender_id)

        if file_type:
            query = query.where(Document.file_type == file_type)

        if search:
            query = query.where(Document.name.ilike(f'%{search}%'))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Document.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await db.execute(query)
        documents = result.scalars().all()

        return list(documents), total

    @staticmethod
    async def update_document(
        db: AsyncSession,
        document_id: UUID,
        **updates,
    ) -> Optional[Document]:
        doc = await FileService.get_document(db, document_id)
        if not doc:
            return None

        for key, value in updates.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        await db.commit()
        await db.refresh(doc)
        logger.info(f'Document updated: {document_id}')
        return doc

    @staticmethod
    async def soft_delete_document(
        db: AsyncSession,
        document_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        doc = await FileService.get_document(db, document_id)
        if not doc:
            return False

        doc.deleted_at = datetime.now(timezone.utc)
        doc.deleted_by_id = deleted_by_id
        await db.commit()
        logger.info(f'Document soft-deleted: {document_id}')
        return True

    @staticmethod
    async def permanent_delete_document(
        db: AsyncSession,
        document_id: UUID,
    ) -> bool:
        result = await db.execute(
            delete(Document).where(Document.id == document_id)
        )
        await db.commit()
        logger.info(f'Document permanently deleted: {document_id}')
        return result.rowcount > 0

    @staticmethod
    async def batch_delete(
        db: AsyncSession,
        document_ids: list[UUID],
    ) -> tuple[int, int]:
        success_count = 0
        fail_count = 0

        for doc_id in document_ids:
            result = await db.execute(
                delete(Document).where(Document.id == doc_id)
            )
            if result.rowcount > 0:
                success_count += 1
            else:
                fail_count += 1

        await db.commit()
        return success_count, fail_count

    @staticmethod
    async def archive_documents(
        db: AsyncSession,
        document_ids: list[UUID],
    ) -> int:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(Document)
            .where(Document.id.in_(document_ids))
            .values(is_archived=True, archived_at=now)
        )
        await db.commit()
        logger.info(f'Documents archived: {len(document_ids)}')
        return result.rowcount

    @staticmethod
    async def track_access(
        db: AsyncSession,
        document_id: UUID,
    ) -> None:
        doc = await FileService.get_document(db, document_id)
        if doc:
            doc.access_count += 1
            doc.last_accessed_at = datetime.now(timezone.utc)
            await db.commit()

    @staticmethod
    async def get_storage_stats(
        db: AsyncSession,
        tenant_id: UUID,
    ) -> dict:
        result = await db.execute(
            select(
                func.count(Document.id).label('total_files'),
                func.sum(Document.file_size).label('total_size'),
                Document.file_type,
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
                Document.is_archived == False,
            )
            .group_by(Document.file_type)
        )
        rows = result.all()

        by_type = {}
        total_files = 0
        total_size = 0

        for row in rows:
            total_files += row.total_files or 0
            total_size += row.total_size or 0
            if row.file_type:
                by_type[row.file_type] = row.total_files or 0

        return {
            'total_files': total_files,
            'total_size_bytes': total_size or 0,
            'total_size_mb': round((total_size or 0) / (1024 * 1024), 2),
            'by_type': by_type,
        }


file_service = FileService()