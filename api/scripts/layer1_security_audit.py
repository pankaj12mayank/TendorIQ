"""Layer 1 security audit (endpoint leakage + auth guard matrix).

Usage:
  python api/scripts/layer1_security_audit.py
  python api/scripts/layer1_security_audit.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def _static_checks(repo_root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    lite_scope = repo_root / 'api' / 'src' / 'core' / 'lite_scope.py'
    auth_dep = repo_root / 'api' / 'src' / 'api' / 'dependencies' / 'auth.py'
    auth_router = repo_root / 'api' / 'src' / 'api' / 'routers' / 'auth.py'
    main_py = repo_root / 'api' / 'src' / 'main.py'

    scope_text = lite_scope.read_text(encoding='utf-8')
    results.append(
        CheckResult(
            'user_scope_no_tenant_fallback_default',
            "include_tenant_fallback: bool = False" in scope_text,
            'lite_scope default include_tenant_fallback should be False',
        )
    )

    dep_text = auth_dep.read_text(encoding='utf-8')
    results.append(
        CheckResult(
            'auth_reads_session_cookie',
            "__session" in dep_text,
            'get_current_user should read __session cookie',
        )
    )

    auth_text = auth_router.read_text(encoding='utf-8')
    results.append(
        CheckResult(
            'auth_sets_http_only_cookie',
            'httponly=True' in auth_text and "set_cookie(" in auth_text,
            'auth router should set HttpOnly session cookies',
        )
    )
    results.append(
        CheckResult(
            'auth_logout_clears_cookie',
            "delete_cookie('__session'" in auth_text,
            'logout should clear __session cookie',
        )
    )

    main_text = main_py.read_text(encoding='utf-8')
    results.append(
        CheckResult(
            'no_store_api_headers_middleware',
            'Cache-Control' in main_text and 'no-store' in main_text,
            'API middleware should set no-store headers',
        )
    )

    return results


def _runtime_checks(base_url: str) -> list[CheckResult]:
    out: list[CheckResult] = []
    s = requests.Session()
    try:
        health = s.get(f'{base_url}/api/v1/health', timeout=8)
        if health.status_code >= 500:
            return [CheckResult('server_reachable', False, f'Health endpoint status {health.status_code}')]
    except Exception as exc:  # noqa: BLE001
        return [CheckResult('server_reachable', False, f'Could not reach server: {exc}')]

    # Public endpoint should work without auth.
    pub = s.get(f'{base_url}/api/v1/public/site', timeout=8)
    out.append(
        CheckResult(
            'public_site_open',
            pub.status_code == 200,
            f'/public/site returned {pub.status_code}',
        )
    )

    # Protected endpoints should not be publicly accessible.
    protected_paths = [
        '/api/v1/auth/me',
        '/api/v1/files/upload/config',
        '/api/v1/proposals/tender/00000000-0000-0000-0000-000000000000',
        '/api/v1/admin/platform/dashboard/overview',
    ]
    for path in protected_paths:
        r = s.get(f'{base_url}{path}', timeout=8)
        out.append(
            CheckResult(
                f'protected_requires_auth:{path}',
                r.status_code in (401, 403),
                f'{path} returned {r.status_code}',
            )
        )

    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://localhost:8000')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    checks = _static_checks(repo_root)
    checks.extend(_runtime_checks(args.base_url))

    passed = [c for c in checks if c.passed]
    failed = [c for c in checks if not c.passed]
    report = {
        'summary': {
            'total': len(checks),
            'passed': len(passed),
            'failed': len(failed),
        },
        'checks': [{'name': c.name, 'passed': c.passed, 'detail': c.detail} for c in checks],
    }
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
