"""Public site endpoint returns defaults (no migration required for read)."""

from fastapi.testclient import TestClient

from src.main import app


def test_public_site_returns_defaults():
    with TestClient(app) as client:
        response = client.get('/api/v1/public/site')
    assert response.status_code == 200
    body = response.json()
    assert body.get('success') is True
    data = body.get('data') or {}
    assert 'landing' in data
    assert 'pricing' in data
