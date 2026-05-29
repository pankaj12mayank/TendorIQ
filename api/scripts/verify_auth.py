"""Verify dev login accounts exist and passwords work. Exit 1 on failure."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


def _api_dir() -> Path:
    return Path(__file__).resolve().parents[1]


async def _verify() -> list[str]:
    api_dir = _api_dir()
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    from src.core.database import async_session_maker
    from src.core.local_user_auth import (
        _owner_defaults,
        authenticate_email_password,
        ensure_dev_accounts,
    )

    owner_email, owner_pass, _ = _owner_defaults()
    errors: list[str] = []

    async with async_session_maker() as db:
        await ensure_dev_accounts(db)
        for email, password in ((owner_email, owner_pass),):
            result = await authenticate_email_password(db, email, password)
            if not result:
                errors.append(f'Login failed for {email} (check .tenderiq/owner-account.txt)')
            else:
                user_payload, _tokens = result
                if email == owner_email and user_payload.get('role') != 'super_admin':
                    errors.append(f'{email} is not platform super_admin')

    return errors


def main() -> int:
    try:
        errors = asyncio.run(_verify())
    except Exception as exc:
        print(f'ERROR: auth verification failed: {exc}', file=sys.stderr)
        return 1

    if errors:
        for err in errors:
            print(f'ERROR: {err}', file=sys.stderr)
        print(
            'Fix: run  cd api && python scripts/ensure_database.py',
            file=sys.stderr,
        )
        return 1

    from src.core.local_user_auth import _owner_defaults, owner_account_file_path

    owner_email, owner_pass, _ = _owner_defaults()
    print(f'OK auth: {owner_email} / {owner_pass}')
    print(f'    file: {owner_account_file_path()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
