from fastapi.testclient import TestClient
from src.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_app_configuration():
    assert app.title == "TenderIQ"
    assert app.version is not None


def test_cors_middleware_loaded():
    from fastapi.middleware.cors import CORSMiddleware
    cors_middleware = [m for m in app.user_middleware if m.cls == CORSMiddleware]
    assert len(cors_middleware) > 0


def test_all_routers_registered():
    routes = [r.path for r in app.routes]
    assert "/health" in routes
    assert "/api/v1/tenders" in routes or "/tenders" in routes
    assert "/api/v1/auth" in routes or "/auth" in routes
