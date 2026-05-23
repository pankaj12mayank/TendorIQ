"""MySQL reachability check and optional database creation for local bootstrap."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def _api_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_database_url() -> str:
    api_dir = _api_dir()
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))
    from src.core.config import settings

    url = (settings.DATABASE_URL or '').strip()
    if not url:
        print('ERROR: DATABASE_URL is empty. Set it in the repo root .env file.', file=sys.stderr)
        sys.exit(1)
    return url


def _parse_mysql_url(url: str) -> dict[str, str | int]:
    raw = re.sub(r'^mysql\+[^:]+://', 'mysql://', url, count=1)
    parsed = urlparse(raw)
    database = (parsed.path or '/').lstrip('/').split('?')[0] or 'tenderiq'
    return {
        'host': parsed.hostname or 'localhost',
        'port': int(parsed.port or 3306),
        'user': unquote(parsed.username or 'root'),
        'password': unquote(parsed.password or ''),
        'database': database,
    }


def _connect_server(cfg: dict[str, str | int]):
    import pymysql

    return pymysql.connect(
        host=str(cfg['host']),
        port=int(cfg['port']),
        user=str(cfg['user']),
        password=str(cfg['password']),
        charset='utf8mb4',
        connect_timeout=5,
    )


def _connect_database(cfg: dict[str, str | int]):
    import pymysql

    return pymysql.connect(
        host=str(cfg['host']),
        port=int(cfg['port']),
        user=str(cfg['user']),
        password=str(cfg['password']),
        database=str(cfg['database']),
        charset='utf8mb4',
        connect_timeout=5,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description='TenderIQ MySQL bootstrap helper')
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Verify server reachability only (do not create database)',
    )
    args = parser.parse_args()

    cfg = _parse_mysql_url(_load_database_url())

    try:
        server = _connect_server(cfg)
    except Exception as exc:
        print(
            f'ERROR: Cannot reach MySQL at {cfg["host"]}:{cfg["port"]} - {exc}',
            file=sys.stderr,
        )
        print(
            'Fix: Start MySQL 8+ and set DATABASE_URL in .env (see docs/MYSQL_SETUP.md).',
            file=sys.stderr,
        )
        return 1

    if not args.check_only:
        db_name = str(cfg['database']).replace('`', '')
        try:
            with server.cursor() as cur:
                cur.execute(
                    f'CREATE DATABASE IF NOT EXISTS `{db_name}` '
                    'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
                )
            server.commit()
            print(f'OK database `{db_name}` ready')
        except Exception as exc:
            print(f'ERROR: Could not create database `{db_name}` - {exc}', file=sys.stderr)
            server.close()
            return 1

    server.close()

    try:
        conn = _connect_database(cfg)
        conn.close()
    except Exception as exc:
        print(
            f'ERROR: Cannot connect to database `{cfg["database"]}` - {exc}',
            file=sys.stderr,
        )
        return 1

    print('OK MySQL')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
