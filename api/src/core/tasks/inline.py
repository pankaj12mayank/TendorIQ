"""In-process background tasks (no Redis/ARQ)."""

import asyncio
import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


async def run_job(function: str, **kwargs: Any) -> None:
    """Execute a registered background job."""
    if function == 'process_ocr_job':
        from ..database import async_session_maker
        from ..ocr.worker import process_ocr_job

        async with async_session_maker() as db:
            try:
                await process_ocr_job(
                    {
                        'db': db,
                        'document_id': kwargs['document_id'],
                        'tenant_id': str(kwargs['tenant_id']),
                        'retry_count': kwargs.get('retry_count', 0),
                    }
                )
                await db.commit()
            except Exception:
                await db.rollback()
                raise
        return

    logger.warning('Unknown or disabled background job: %s', function)


def schedule_job(function: str, **kwargs: Any) -> str:
    """Fire-and-forget on the running event loop. Returns a local job id."""
    job_id = kwargs.pop('_job_id', None) or str(uuid4())
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_run_safe(function, job_id, **kwargs))
    except RuntimeError:
        logger.warning('No event loop — cannot schedule job %s', function)
    return job_id


async def _run_safe(function: str, job_id: str, **kwargs: Any) -> None:
    try:
        await run_job(function, **kwargs)
    except Exception:
        logger.exception('Background job %s (%s) failed', function, job_id)
