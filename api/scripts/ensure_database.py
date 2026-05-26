"""Local database bootstrap: SQLite (default dev) or MySQL."""

from __future__ import annotations

import sys
from pathlib import Path


def _api_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    api_dir = _api_dir()
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    from src.core.config import get_settings

    settings = get_settings()

    url = (settings.DATABASE_URL or '').strip()
    if not url:
        print('ERROR: DATABASE_URL is empty. Set DATABASE_DRIVER=sqlite or MYSQL_PASSWORD in .env', file=sys.stderr)
        return 1

    if url.startswith('sqlite'):
        return _ensure_sqlite(api_dir)

    return _ensure_mysql()


def _ensure_sqlite(api_dir: Path) -> int:
    try:
        import aiosqlite  # noqa: F401
    except ImportError:
        print(
            'ERROR: aiosqlite is not installed. Run: run.bat setup  (or pip install aiosqlite)',
            file=sys.stderr,
        )
        return 1

    from sqlalchemy import create_engine, text

    from src.core.config import _PROJECT_ROOT, get_settings
    from src.core.models import Base

    settings = get_settings()

    raw = settings.database_url_sync
    db_path = raw.replace('sqlite:///', '').split('?')[0]
    path = Path(db_path)
    if not path.is_absolute():
        path = (_PROJECT_ROOT / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings.database_url_sync)
    try:
        with engine.begin() as conn:
            conn.execute(text('SELECT 1'))
            Base.metadata.create_all(bind=conn)
    except Exception as exc:
        print(f'ERROR: SQLite setup failed at {path} - {exc}', file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    code = _seed_password_users_if_empty()
    if code != 0:
        return code

    print(f'OK SQLite database at {path}')
    return 0


def _seed_password_users_if_empty() -> int:
    import asyncio

    from src.core.database import async_session_maker
    from src.core.local_user_auth import seed_initial_accounts_if_empty

    async def _run() -> bool:
        async with async_session_maker() as session:
            return await seed_initial_accounts_if_empty(session)

    try:
        created = asyncio.run(_run())
    except Exception as exc:
        print(f'ERROR: user seed failed - {exc}', file=sys.stderr)
        return 1
    if created:
        print('INFO: system owner login -> .tenderiq/owner-account.txt')
    return 0


def _ensure_mysql() -> int:
    import ensure_mysql as mysql_script

    return mysql_script.main()


if __name__ == '__main__':
    raise SystemExit(main())
