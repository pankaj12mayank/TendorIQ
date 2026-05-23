"""OpenAPI contract — FE-critical routes are published."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

CONTRACT_PATH = Path(__file__).resolve().parents[1] / 'contracts' / 'fe_api_paths.json'


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


def test_openapi_spec_available(api_client):
    response = api_client.get('/openapi.json')
    assert response.status_code == 200
    assert 'paths' in response.json()


def test_openapi_includes_fe_contract_paths(api_client):
    spec_paths = api_client.get('/openapi.json').json()['paths']
    missing = [p for p in _load_contract_paths() if p not in spec_paths]
    assert not missing, f'Missing OpenAPI paths: {missing}'


def test_tenders_route_requires_auth(api_client):
    response = api_client.get('/api/v1/tenders')
    assert response.status_code in (401, 403)


def test_error_envelope_shape_on_validation(api_client):
    response = api_client.post('/api/v1/auth/login', json={})
    assert response.status_code == 422
    body = response.json()
    assert body.get('success') is False
    assert 'error' in body
