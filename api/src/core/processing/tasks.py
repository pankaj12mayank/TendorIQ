"""Background analysis tasks (fire-and-forget after upload)."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional
from uuid import UUID

from ..config import settings
from ..database import async_session_maker
from .document_analyzer import run_document_analysis

logger = logging.getLogger(__name__)

_running: set[str] = set()


async def schedule_document_analysis(
    *,
    document_id: str,
    tenant_id: str,
    owner_id: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    """Queue analysis unless already running for this document."""
    if not settings.AI_AUTO_ANALYZE_ON_UPLOAD:
        return
    if document_id in _running:
        return
    _running.add(document_id)
    asyncio.create_task(
        _run_analysis_task(
            document_id=document_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            provider=provider,
            model=model,
        )
    )


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
    except Exception as exc:
        logger.error('Background analysis failed for %s: %s', document_id, exc)
    finally:
        _running.discard(document_id)
