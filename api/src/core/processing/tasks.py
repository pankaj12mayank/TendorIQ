"""Background analysis tasks (fire-and-forget after upload)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update

from ..config import settings
from ..database import async_session_maker
from .document_analyzer import run_document_analysis

logger = logging.getLogger(__name__)

STUCK_TIMEOUT_MINUTES = 30


async def schedule_document_analysis(
    *,
    document_id: str,
    tenant_id: str,
    owner_id: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    force: bool = False,
) -> None:
    """Queue analysis unless already running for this document (atomic check-and-set)."""
    if not settings.AI_AUTO_ANALYZE_ON_UPLOAD and not force:
        return
    async with async_session_maker() as db:
        from ..models import Document

        result = await db.execute(
            update(Document)
            .where(
                Document.id == UUID(document_id),
                Document.processing_status.notin_(('queued', 'processing', 'retrying')),
            )
            .values(processing_status='queued')
        )
        if result.rowcount == 0:
            return
        await db.commit()
    asyncio.create_task(
        _run_analysis_task(
            document_id=document_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            provider=provider,
            model=model,
        )
    )


async def recover_stuck_documents() -> int:
    """Recover documents stuck in non-terminal states (e.g. after restart).
    
    Marks documents that have been in 'queued', 'extracting', 'processing', or 
    'validating' for longer than STUCK_TIMEOUT_MINUTES as 'failed'.
    Returns count of recovered documents.
    """
    stuck_states = ('queued', 'extracting', 'processing', 'validating')
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STUCK_TIMEOUT_MINUTES)
    try:
        async with async_session_maker() as db:
            from ..models import Document

            result = await db.execute(
                select(Document).where(
                    Document.processing_status.in_(stuck_states),
                    Document.updated_at < cutoff,
                )
            )
            stuck = result.scalars().all()
            if not stuck:
                return 0

            for doc in stuck:
                doc.processing_status = 'failed'
                doc.processing_error = (
                    f'Processing timed out after {STUCK_TIMEOUT_MINUTES} minutes '
                    f'(state was "{doc.processing_status}"). Please retry.'
                )
            await db.commit()
            logger.info('Recovered %d stuck document(s)', len(stuck))
            return len(stuck)
    except Exception as exc:
        logger.error('Failed to recover stuck documents: %s', exc)
        return 0


async def _run_analysis_task(
    *,
    document_id: str,
    tenant_id: str,
    owner_id: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    try:
        async with async_session_maker() as db:
            await run_document_analysis(
                db,
                document_id=UUID(document_id),
                tenant_id=UUID(tenant_id),
                owner_id=UUID(owner_id),
                provider=provider,
                model=model,
            )
        logger.info('Background analysis completed for document %s', document_id)
        status = 'completed'
    except Exception as exc:
        logger.error('Background analysis failed for %s: %s', document_id, exc)
        status = 'failed'
    finally:
        async with async_session_maker() as db:
            from ..models import Document, pk_str

            doc = await db.get(Document, pk_str(document_id))
            if doc:
                doc.processing_status = status
                await db.commit()
