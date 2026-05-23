"""OpenAPI contract — FE-critical routes are published."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

CONTRACT_PATH = Path(__file__).resolve().parents[1] / 'contracts' / 'fe_api_paths.json'
WEB_SRC = Path(__file__).resolve().parents[4] / 'apps' / 'web' / 'src'


@pytest.fixture(scope='module')
def api_client():
    try:
        from src.main import app
    except ImportError as exc:
        pytest.skip(f'API runtime dependencies unavailable: {exc}')
    return TestClient(app)


def _load_contract_paths() -> list[str]:
    data = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    return list(data['paths'])


def _openapi_paths(client: TestClient) -> set[str]:
    return set(client.get('/openapi.json').json()['paths'].keys())


def _path_covered(spec_paths: set[str], contract_path: str) -> bool:
    if contract_path in spec_paths:
        return True
    base = contract_path.rstrip('/')
    for spec in spec_paths:
        if spec == base or spec.startswith(base + '/'):
            return True
    return False


def test_openapi_spec_available(api_client):
    response = api_client.get('/openapi.json')
    assert response.status_code == 200
    assert 'paths' in response.json()


def test_openapi_includes_fe_contract_paths(api_client):
    spec_paths = _openapi_paths(api_client)
    missing = [p for p in _load_contract_paths() if not _path_covered(spec_paths, p)]
    assert not missing, f'Missing OpenAPI paths (prefix match): {missing}'


def test_bids_route_registered(api_client):
    spec_paths = _openapi_paths(api_client)
    assert _path_covered(spec_paths, '/api/v1/bids')


def test_webhooks_routes_registered(api_client):
    spec_paths = _openapi_paths(api_client)
    assert _path_covered(spec_paths, '/api/v1/webhooks/stripe')
    assert _path_covered(spec_paths, '/api/v1/webhooks/resend')
    assert '/api/v1/webhooks/clerk' not in spec_paths


def test_web_paths_in_contract_or_openapi(api_client):
    """Surface FE /api/v1/* usage not listed in fe_api_paths.json (L3-5)."""
    if not WEB_SRC.is_dir():
        pytest.skip('web src not present')
    spec_paths = _openapi_paths(api_client)
    contract = set(_load_contract_paths())
    used: set[str] = set()
    pattern = re.compile(r"['\"](/api/v1/[^'\"]+)['\"]")
    for path in WEB_SRC.rglob('*'):
        if path.suffix not in ('.ts', '.tsx'):
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for match in pattern.findall(text):
            used.add(match.split('?')[0].rstrip('/'))

    undocumented = sorted(
        p
        for p in used
        if not any(p == c or p.startswith(c.rstrip('/') + '/') or c.startswith(p) for c in contract)
        and not _path_covered(spec_paths, p)
    )
    assert not undocumented, f'Web uses API paths missing from contract and OpenAPI: {undocumented[:20]}'


def test_tenders_route_requires_auth(api_client):
    response = api_client.get('/api/v1/tenders')
    assert response.status_code in (401, 403)


def test_bids_route_requires_auth(api_client):
    response = api_client.get('/api/v1/bids')
    assert response.status_code in (401, 403)


def test_error_envelope_shape_on_validation(api_client):
    response = api_client.post('/api/v1/auth/login', json={})
    assert response.status_code == 422
    body = response.json()
    assert body.get('success') is False
    assert 'error' in body
