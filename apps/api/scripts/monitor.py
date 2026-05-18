#!/usr/bin/env python
"""Queue Monitoring Dashboard (CLI)

Usage:
    python scripts/monitor.py stats              # Overall stats
    python scripts/monitor.py queue <name>       # Queue details
    python scripts/monitor.py alerts             # Active alerts
    python scripts/monitor.py dead-letter        # Dead letter jobs
    python scripts/monitor.py health              # System health
    python scripts/monitor.py throughput         # Throughput stats
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.queue.monitoring import QueueMonitor, AlertHandler
from src.core.queue.dead_letter import DeadLetterHandler, FailedJobsHandler
from src.core.queue.config import QueueConfig


def print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, default=str))


def print_table(data: list[dict], headers: list[str]) -> None:
    if not data:
        print('No data')
        return

    col_widths = [len(h) for h in headers]
    for row in data:
        for i, h in enumerate(headers):
            key = h.lower().replace(' ', '_')
            val = str(row.get(key, ''))[:30]
            col_widths[i] = max(col_widths[i], len(val))

    header_row = ' | '.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = '-+-'.join('-' * w for w in col_widths)

    print(header_row)
    print(separator)

    for row in data:
        cols = []
        for i, h in enumerate(headers):
            key = h.lower().replace(' ', '_')
            val = str(row.get(key, ''))[:col_widths[i]]
            cols.append(val.ljust(col_widths[i]))
        print(' | '.join(cols))


async def cmd_stats():
    monitor = QueueMonitor()
    try:
        stats = await monitor.get_stats()
        print_json(stats)
    finally:
        await monitor.close()


async def cmd_queue_details(queue_name: str):
    monitor = QueueMonitor()
    try:
        details = await monitor.get_queue_details(queue_name)
        print_json(details)
    finally:
        await monitor.close()


async def cmd_alerts():
    alerts = await AlertHandler.get_queue_alerts()

    if not alerts:
        print('No active alerts')
        return

    print(f'Active Alerts: {len(alerts)}')
    for alert in alerts:
        severity = alert['severity'].upper()
        print(f'[{severity}] {alert["queue"]}: {alert["message"]}')


async def cmd_dead_letter(limit: int = 10):
    handler = DeadLetterHandler()
    try:
        items = await handler.get_dead_letters(limit=limit)
        print(f'Dead Letter Queue: {len(items)} jobs')

        if items:
            print('\nRecent Jobs:')
            for item in items[:limit]:
                print(f"  {item['job_id']}: {item['job_name']} - {item['error'][:50]}...")
    finally:
        await handler.close()


async def cmd_health():
    health = await AlertHandler.check_health()
    print_json(health)


async def cmd_throughput(hours: int = 24):
    monitor = QueueMonitor()
    try:
        stats = await monitor.get_throughput_stats(hours=hours)
        print_json(stats)
    finally:
        await monitor.close()


async def cmd_workers():
    monitor = QueueMonitor()
    try:
        status = await monitor.get_worker_status()
        print_json(status)
    finally:
        await monitor.close()


async def cmd_slow_jobs(threshold: int = 300):
    monitor = QueueMonitor()
    try:
        jobs = await monitor.get_slow_jobs(threshold_seconds=threshold)
        print(f'Slow Jobs (> {threshold}s): {len(jobs)}')

        if jobs:
            print('\nSlowest Jobs:')
            for job in jobs[:10]:
                print(f"  {job.get('job_id')}: {job.get('elapsed_seconds')}s elapsed")
    finally:
        await monitor.close()


async def cmd_failed(limit: int = 10):
    handler = FailedJobsHandler()
    try:
        items = await handler.get_failed_jobs(limit=limit)
        stats = await handler.get_failed_stats()

        print(f'Failed Jobs: {stats["total"]}')
        print(f'By Type: {stats["by_job"]}')

        if items:
            print('\nRecent Failures:')
            for item in items[:limit]:
                print(f"  {item['job_id']}: {item['job_name']}")
    finally:
        await handler.close()


def main():
    parser = argparse.ArgumentParser(description='Queue Monitor')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('stats', help='Overall queue statistics')
    subparsers.add_parser('alerts', help='Active alerts')
    subparsers.add_parser('health', help='System health check')
    subparsers.add_parser('workers', help='Worker status')

    queue_parser = subparsers.add_parser('queue', help='Queue details')
    queue_parser.add_argument('name', help='Queue name (ocr, parsing, email, analysis, notifications)')

    dl_parser = subparsers.add_parser('dead-letter', help='Dead letter queue')
    dl_parser.add_argument('-n', '--limit', type=int, default=10, help='Limit results')

    tp_parser = subparsers.add_parser('throughput', help='Throughput stats')
    tp_parser.add_argument('--hours', type=int, default=24, help='Time window')

    slow_parser = subparsers.add_parser('slow', help='Slow jobs')
    slow_parser.add_argument('--threshold', type=int, default=300, help='Threshold in seconds')

    failed_parser = subparsers.add_parser('failed', help='Failed jobs')
    failed_parser.add_argument('-n', '--limit', type=int, default=10, help='Limit results')

    args = parser.parse_args()

    commands = {
        'stats': cmd_stats,
        'queue': lambda: cmd_queue_details(args.name),
        'alerts': cmd_alerts,
        'health': cmd_health,
        'throughput': lambda: cmd_throughput(args.hours),
        'workers': cmd_workers,
        'slow': lambda: cmd_slow_jobs(args.threshold),
        'dead-letter': lambda: cmd_dead_letter(args.limit),
        'failed': lambda: cmd_failed(args.limit),
    }

    cmd = commands.get(args.command)
    if cmd:
        asyncio.run(cmd())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()