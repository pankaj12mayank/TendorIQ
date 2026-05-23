"""Health and app smoke tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope='module')
def api_client():
    try:
        from src.main import app
    except ImportError as exc:
        pytest.skip(f'API runtime dependencies unavailable: {exc}')
    return TestClient(app)


@pytest.fixture(scope='module')
def app_title(api_client):
    from src.main import app

    return app.title


def test_health_endpoint_returns_ok(api_client):
    response = api_client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'


def test_app_title(app_title):
    assert app_title == 'TenderIQ'


def test_core_routers_registered(api_client):
    from src.main import app

    routes = {r.path for r in app.routes}
    assert '/health' in routes
    assert '/api/v1/tenders' in routes
