"""Health endpoint smoke tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client():
    from src.main import app

    return TestClient(app)


def test_health_endpoint(api_client):
    response = api_client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


def test_readiness_endpoint_reports_database(api_client):
    response = api_client.get('/health/ready')
    assert response.status_code in (200, 503)
    data = response.json()
    assert 'checks' in data
    assert 'database' in data['checks']


def test_app_configuration(api_client):
    from src.main import app

    assert app.title == 'TenderIQ'
    assert app.version is not None


def test_cors_middleware_loaded():
    from fastapi.middleware.cors import CORSMiddleware
    from src.main import app

    cors_middleware = [m for m in app.user_middleware if m.cls == CORSMiddleware]
    assert len(cors_middleware) > 0


def test_all_routers_registered(api_client):
    from src.main import app

    routes = [r.path for r in app.routes]
    assert '/health' in routes
    assert '/api/v1/tenders' in routes or any('tenders' in r for r in routes)
    assert any('/api/v1' in r and 'auth' in r for r in routes)
