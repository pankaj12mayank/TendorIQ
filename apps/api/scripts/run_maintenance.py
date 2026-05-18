#!/usr/bin/env python
"""Scheduled Maintenance Script

Usage:
    python scripts/run_maintenance.py --hourly   # Hourly tasks
    python scripts/run_maintenance.py --daily    # Daily tasks
    python scripts/run_maintenance.py --weekly   # Weekly tasks
    python scripts/run_maintenance.py --health   # Health check only
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.queue.recovery import AutomaticRecovery, MaintenanceScheduler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def run_hourly():
    logger.info('Running hourly maintenance...')
    result = await MaintenanceScheduler.run_hourly_maintenance()
    logger.info(f'Hourly maintenance completed: {result}')
    return result


async def run_daily():
    logger.info('Running daily maintenance...')
    result = await MaintenanceScheduler.run_daily_maintenance()
    logger.info(f'Daily maintenance completed: {result}')
    return result


async def run_weekly():
    logger.info('Running weekly maintenance...')

    results = {}

    results['daily_maintenance'] = await MaintenanceScheduler.run_daily_maintenance()

    from src.core.queue.dead_letter import DeadLetterHandler, FailedJobsHandler
    from src.core.queue.config import REDIS_POOL_MAIN

    pool = await import('redis.asyncio').create_pool(REDIS_POOL_MAIN)
    try:
        dl_handler = DeadLetterHandler(pool)
        fj_handler = FailedJobsHandler(pool)

        results['dead_letter_cleanup'] = await dl_handler.discard_all()
        results['failed_jobs_cleanup'] = await fj_handler.clear_failed_jobs(older_than_days=7)

        results['recovery_history_clear'] = True
    finally:
        await pool.aclose()

    logger.info(f'Weekly maintenance completed: {results}')
    return results


async def check_health():
    logger.info('Running health check...')
    auto = AutomaticRecovery()
    health = await auto.get_system_health()
    logger.info(f'Health check result: {health}')

    if health['status'] != 'healthy':
        logger.warning(f'System health is {health["status"]}')
        logger.warning(f'Issues: {health["checks"]}')
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description='Queue Maintenance')
    parser.add_argument('--hourly', action='store_true', help='Run hourly tasks')
    parser.add_argument('--daily', action='store_true', help='Run daily tasks')
    parser.add_argument('--weekly', action='store_true', help='Run weekly tasks')
    parser.add_argument('--health', action='store_true', help='Health check only')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    if not any([args.hourly, args.daily, args.weekly, args.health]):
        parser.print_help()
        sys.exit(0)

    if args.health:
        result = asyncio.run(check_health())
        sys.exit(0 if result else 1)

    if args.hourly:
        asyncio.run(run_hourly())

    if args.daily:
        asyncio.run(run_daily())

    if args.weekly:
        asyncio.run(run_weekly())


if __name__ == '__main__':
    main()