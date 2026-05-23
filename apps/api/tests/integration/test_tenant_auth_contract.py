"""Integration-style HTTP contract tests (no database required)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope='module')
def api_client():
    try:
        from src.main import app
    except ImportError as exc:
        pytest.skip(f'API runtime dependencies unavailable: {exc}')
    return TestClient(app)


def test_protected_tenant_routes_reject_anonymous(api_client):
    for path, method in (
        ('/api/v1/tenders', 'get'),
        ('/api/v1/notifications', 'get'),
        ('/api/v1/billing/plans', 'get'),
    ):
        response = getattr(api_client, method)(path)
        assert response.status_code in (401, 403), f'{method.upper()} {path} => {response.status_code}'


def test_auth_login_route_exists(api_client):
    response = api_client.post(
        '/api/v1/auth/login',
        json={'email': 'nobody@example.com', 'password': 'wrong-password-123'},
    )
    assert response.status_code in (400, 401, 422, 500)
