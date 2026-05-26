"""End-to-end auth: login → /me → refresh (in-process ASGI)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_login_me_refresh_flow():
    from src.core.database import _ensure_dev_accounts_on_startup
    from src.main import app

    await _ensure_dev_accounts_on_startup()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        login = await client.post(
            '/api/v1/auth/login',
            json={'email': 'admin@tendoriq.com', 'password': 'Owner@ChangeMe123'},
        )
        assert login.status_code == 200, login.text
        body = login.json()
        token = body.get('access_token') or body.get('token')
        assert token
        assert body.get('user', {}).get('role') == 'super_admin'

        me = await client.get(
            '/api/v1/auth/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert me.status_code == 200, me.text
        me_body = me.json()
        assert me_body.get('email') == 'admin@tendoriq.com'
        assert me_body.get('role') == 'super_admin'

        refresh = body.get('refresh_token')
        assert refresh
        refreshed = await client.post(
            '/api/v1/auth/refresh',
            json={'refresh_token': refresh},
        )
        assert refreshed.status_code == 200, refreshed.text
        assert refreshed.json().get('access_token')
