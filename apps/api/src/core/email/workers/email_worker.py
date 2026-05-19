"""ARQ worker entry for processing email queue items."""

import logging

logger = logging.getLogger(__name__)


async def process_email_queue(ctx: dict, queue_item_id: str, **kwargs) -> dict:
    from ...database import async_session_maker
    from ..services.processor import EmailProcessor

    async with async_session_maker() as db:
        processor = EmailProcessor(db)
        return await processor.process_queue_item(queue_item_id)
