"""HTTP smoke test: login + /me against running API. Exit 1 on failure."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
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


def _post_form(url: str, payload: dict[str, str]) -> dict:
    data = urllib.parse.urlencode(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
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

    login_url = f'{base}/api/v1/auth/login'
    try:
        login = _post(login_url, {'email': email, 'password': password})
    except urllib.error.HTTPError as exc:
        # Some local stacks expose an OAuth2 form-style login contract.
        if exc.code == 422:
            try:
                login = _post_form(login_url, {'username': email, 'password': password})
            except urllib.error.URLError as inner_exc:
                print(f'FAIL: API not reachable at {base} — {inner_exc}', file=sys.stderr)
                print('Start: run.bat', file=sys.stderr)
                return 1
            except urllib.error.HTTPError as inner_exc:
                print(f'FAIL: login returned {inner_exc.code}', file=sys.stderr)
                return 1
        else:
            print(f'FAIL: login returned {exc.code}', file=sys.stderr)
            return 1
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
