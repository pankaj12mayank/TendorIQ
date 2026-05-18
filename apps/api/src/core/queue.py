"""Task Queue with ARQ"""

import logging
from datetime import datetime
from typing import Any, Optional

from arq import Actor
from arq.connections import RedisSettings

from .config import settings
from .logging import get_logger

logger = get_logger('queue')


class WorkerSettings:
    """ARQ Worker Settings"""

    redis_settings = RedisSettings.from_url(
        settings.redis_url,
        use_fakeredis=settings.NODE_ENV == 'development',
    )

    job_timeout = 300
    max_jobs = 10
    keep_result_days = 7

    functions = []


class TaskWorker(Actor):
    """Base task worker with common functionality"""

    async def startup(self) -> None:
        logger.info('Task worker starting up')

    async def shutdown(self) -> None:
        logger.info('Task worker shutting down')


async def enqueue_task(
    task_name: str,
    *args: Any,
    _delay: Optional[int] = None,
    **kwargs: Any,
) -> str:
    """Enqueue a task for background processing"""
    from .redis import get_arq_pool

    pool = get_arq_pool()
    job = await pool.enqueue_job(
        task_name,
        *args,
        _delay=_delay,
        **kwargs,
    )
    return job.id


async def send_tender_notification(tender_id: str, event: str, recipients: list[str]) -> None:
    """Send notification about tender events"""
    await enqueue_task(
        'send_tender_notification',
        tender_id=tender_id,
        event=event,
        recipients=recipients,
    )


async def generate_tender_document(tender_id: str, template: str) -> None:
    """Generate tender document in background"""
    await enqueue_task(
        'generate_tender_document',
        tender_id=tender_id,
        template=template,
    )


async def process_bid_ai_analysis(bid_id: str) -> None:
    """Process bid with AI analysis"""
    await enqueue_task(
        'process_bid_ai_analysis',
        bid_id=bid_id,
    )


async def cleanup_old_attachments(organization_id: str, days: int = 30) -> None:
    """Clean up old attachments"""
    await enqueue_task(
        'cleanup_old_attachments',
        organization_id=organization_id,
        days=days,
    )


class Tasks:
    """Task definitions for ARQ"""

    @staticmethod
    async def send_tender_notification(
        ctx: dict,
        tender_id: str,
        event: str,
        recipients: list[str],
    ) -> dict:
        logger.info(f'Sending tender notification: {tender_id} - {event}')
        return {'status': 'sent', 'recipients': len(recipients)}

    @staticmethod
    async def generate_tender_document(
        ctx: dict,
        tender_id: str,
        template: str,
    ) -> dict:
        logger.info(f'Generating tender document: {tender_id}')
        return {'status': 'generated', 'tender_id': tender_id}

    @staticmethod
    async def process_bid_ai_analysis(ctx: dict, bid_id: str) -> dict:
        logger.info(f'Processing bid AI analysis: {bid_id}')

        from ..api.schemas.tender import TenderBase
        from ..api.services.base import BaseService
        from ..core.database import get_db_session

        async with get_db_session() as db:
            pass

        return {'status': 'processed', 'bid_id': bid_id}

    @staticmethod
    async def cleanup_old_attachments(
        ctx: dict,
        organization_id: str,
        days: int,
    ) -> dict:
        logger.info(f'Cleaning up attachments older than {days} days')
        return {'status': 'cleaned', 'organization_id': organization_id}