import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.core.database import get_session


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_app_title():
    assert app.title == "TenderIQ"


@pytest.mark.asyncio
async def test_routers_are_loaded():
    routes = [r.path for r in app.routes]
    assert "/health" in routes
    assert len(app.routes) > 10
