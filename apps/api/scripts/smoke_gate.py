"""API smoke for client-ready gate G4 (flows 1, 5–8 at HTTP level)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _req(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    token: str | None = None,
    timeout: float = 15.0,
) -> tuple[int, dict | str]:
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8')
            if not raw:
                return resp.status, {}
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='replace')
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, raw


def _token_from_login(payload: dict) -> str:
    if payload.get('access_token'):
        return str(payload['access_token'])
    if payload.get('token'):
        return str(payload['token'])
    data = payload.get('data')
    if isinstance(data, dict):
        return _token_from_login(data)
    raise RuntimeError(f'Login response missing token: {payload!r}')


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    _load_dotenv(repo / '.env')

    api = (os.environ.get('API_URL') or os.environ.get('NEXT_PUBLIC_API_URL') or 'http://127.0.0.1:8000').rstrip(
        '/'
    )
    demo_email = os.environ.get('DEMO_USER_EMAIL') or 'demo@tendoriq.com'
    demo_password = os.environ.get('DEMO_USER_PASSWORD') or 'Demo@123'
    admin_email = os.environ.get('SUPER_ADMIN_EMAIL') or 'admin@tendoriq.com'
    admin_password = os.environ.get('SUPER_ADMIN_PASSWORD') or 'SuperAdmin@123'

    failures: list[str] = []

    # Flow 8 - health
    code, health = _req('GET', f'{api}/health')
    if code != 200 or (isinstance(health, dict) and health.get('status') != 'healthy'):
        failures.append(f'GET /health -> {code} {health}')
    code, ready = _req('GET', f'{api}/health/ready')
    if code != 200:
        failures.append(f'GET /health/ready -> {code} (expected 200 when MySQL up)')
    elif isinstance(ready, dict) and not ready.get('checks', {}).get('database'):
        failures.append(f'/health/ready database check false: {ready}')

    # Flow 1 - sign-in (demo)
    code, login = _req('POST', f'{api}/api/v1/auth/login', body={'email': demo_email, 'password': demo_password})
    if code != 200:
        failures.append(f'DEMO login -> {code} {login}')
        demo_token = None
    else:
        try:
            demo_token = _token_from_login(login if isinstance(login, dict) else {})
        except RuntimeError as exc:
            failures.append(str(exc))
            demo_token = None

    # Flow 2 - tenders
    if demo_token:
        code, tenders = _req('GET', f'{api}/api/v1/tenders', token=demo_token)
        if code not in (200, 404):
            failures.append(f'GET /api/v1/tenders -> {code}')

    # Flow 5 - billing
    if demo_token:
        code, _ = _req('GET', f'{api}/api/v1/billing/plans', token=demo_token)
        if code not in (200, 401, 403):
            failures.append(f'GET /api/v1/billing/plans -> {code}')

    # Flow 6-7 - super admin platform
    code, admin_login = _req(
        'POST', f'{api}/api/v1/auth/login', body={'email': admin_email, 'password': admin_password}
    )
    if code != 200:
        failures.append(f'SUPER_ADMIN login -> {code} {admin_login}')
        admin_token = None
    else:
        try:
            admin_token = _token_from_login(admin_login if isinstance(admin_login, dict) else {})
        except RuntimeError as exc:
            failures.append(str(exc))
            admin_token = None

    if admin_token:
        for path in (
            '/api/v1/admin/platform/users',
            '/api/v1/admin/platform/queue/jobs',
            '/api/v1/email/templates',
        ):
            code, _ = _req('GET', f'{api}{path}', token=admin_token)
            if code not in (200, 404):
                failures.append(f'GET {path} -> {code}')

    if failures:
        print('[G4 FAIL] API smoke:', file=sys.stderr)
        for item in failures:
            print(f'  - {item}', file=sys.stderr)
        return 1

    print('[G4 OK] API smoke: health, demo login, tenders, billing, admin platform, email templates')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
