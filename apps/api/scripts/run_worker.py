#!/usr/bin/env python
"""ARQ Worker Startup Script

Usage:
    python scripts/run_worker.py                    # All queues
    python scripts/run_worker.py --queue ocr         # Specific queue
    python scripts/run_worker.py --queue ocr,parsing # Multiple queues
    python scripts/run_worker.py --watch            # Watch mode (dev)
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from arq.connections import create_pool

from src.core.queue.config import (
    REDIS_POOL_MAIN,
    QUEUE_OCR,
    QUEUE_PARSING,
    QUEUE_EMAIL,
    QUEUE_ANALYSIS,
    QUEUE_NOTIFICATIONS,
)
from src.core.queue.worker_settings import WorkerSettings


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def run_worker(queues: list[str]) -> None:
    logger.info(f'Starting ARQ worker for queues: {queues}')

    pool = await create_pool(REDIS_POOL_MAIN)

    async def run():
        from arq.worker import Worker

        worker = Worker(
            functions=WorkerSettings.functions,
            redis_pool=pool,
            queue_settings=WorkerSettings.queue_settings,
            max_jobs=WorkerSettings.max_jobs,
            job_timeout=WorkerSettings.job_timeout,
            keep_result=WorkerSettings.keep_result,
            keep_failed=WorkerSettings.keep_failed,
            allow_abort=WorkerSettings.allow_abort,
            max_retries=WorkerSettings.max_retries,
            health_check_interval=WorkerSettings.health_check_interval,
            max_concurrent_tasks=WorkerSettings.max_concurrent_tasks,
            on_startup=WorkerSettings.on_worker_start,
            on_shutdown=WorkerSettings.on_worker_shutdown,
            on_job_start=WorkerSettings.on_job_start,
            on_job_end=WorkerSettings.on_job_end,
            on_job_retry=WorkerSettings.on_job_retry,
            before_job_execute=WorkerSettings.before_job_execute,
            after_job_execute=WorkerSettings.after_job_execute,
        )
        await worker.run()

    try:
        await run()
    except KeyboardInterrupt:
        logger.info('Worker shutdown requested')
    finally:
        await pool.aclose()


def signal_handler(signum, frame):
    logger.info(f'Received signal {signum}, shutting down...')
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='ARQ Worker')
    parser.add_argument(
        '--queue',
        '-q',
        type=str,
        default='all',
        help='Queue(s) to process: ocr, parsing, email, analysis, notifications, or all',
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging',
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger('arq').setLevel(logging.DEBUG)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    queue_map = {
        'ocr': QUEUE_OCR,
        'parsing': QUEUE_PARSING,
        'email': QUEUE_EMAIL,
        'analysis': QUEUE_ANALYSIS,
        'notifications': QUEUE_NOTIFICATIONS,
    }

    if args.queue == 'all':
        queues = list(queue_map.values())
    else:
        requested = [q.strip() for q in args.queue.split(',')]
        queues = [queue_map[q] for q in requested if q in queue_map]

    if not queues:
        logger.error(f'Invalid queue specified. Valid options: {list(queue_map.keys())}')
        sys.exit(1)

    asyncio.run(run_worker(queues))


if __name__ == '__main__':
    main()