"""Background Task Scheduler using ARQ"""

import logging
from typing import Any

from arq import Actor

logger = logging.getLogger(__name__)

_scheduler = None


def init_scheduler() -> None:
    global _scheduler
    logger.info('Scheduler initialized (no jobs configured)')


async def close_scheduler() -> None:
    global _scheduler
    _scheduler = None
    logger.info('Scheduler closed')


class TaskWorker(Actor):
    async def startup(self) -> None:
        logger.info('Task worker starting...')

    async def shutdown(self) -> None:
        logger.info('Task worker shutting down...')