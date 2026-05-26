"""HTTP smoke test: login + /me against running API. Exit 1 on failure."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        method='GET',
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000').rstrip('/')
    email = 'admin@tendoriq.com'
    password = 'Owner@ChangeMe123'

    try:
        login = _post(f'{base}/api/v1/auth/login', {'email': email, 'password': password})
    except urllib.error.URLError as exc:
        print(f'FAIL: API not reachable at {base} — {exc}', file=sys.stderr)
        print('Start: run.bat', file=sys.stderr)
        return 1

    token = login.get('access_token') or login.get('token')
    if not token:
        print('FAIL: login response missing token', file=sys.stderr)
        return 1

    try:
        me = _get(f'{base}/api/v1/auth/me', token)
    except urllib.error.HTTPError as exc:
        print(f'FAIL: /me returned {exc.code}', file=sys.stderr)
        return 1

    if me.get('email') != email:
        print(f'FAIL: /me email mismatch {me!r}', file=sys.stderr)
        return 1

    print(f'OK auth flow: {email} → login → /me (role={me.get("role")})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
