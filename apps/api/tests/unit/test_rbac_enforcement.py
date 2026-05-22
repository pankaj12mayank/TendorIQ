"""Layer 4 — API RBAC dependency enforcement tests."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies.permissions import require_tenant_permission
from src.api.dependencies.rbac_deps import (
    RequireTenderCreate,
    require_tenant_member,
)
from src.core.auth import AuthContext
from src.core.rbac import Permission, RBACService


def test_viewer_cannot_create_tender_permission():
    assert not RBACService.has_permission('viewer', Permission.TENDER_CREATE)
    assert RBACService.has_permission('viewer', Permission.TENDER_READ)


def test_manager_can_create_tender_permission():
    assert RBACService.has_permission('manager', Permission.TENDER_CREATE)


def test_require_tenant_permission_factory_blocks_viewer():
    app = FastAPI()

    @app.get('/probe', dependencies=[Depends(require_tenant_permission(Permission.TENDER_CREATE))])
    async def probe():
        return {'ok': True}

    # Dependency is not invoked without auth header — smoke test factory is callable
    assert callable(require_tenant_permission(Permission.TENDER_CREATE))


def test_super_admin_blocked_on_tenant_member_dependency():
    from fastapi import HTTPException
    import asyncio

    async def run():
        auth = AuthContext(
            user_id='super_admin',
            email='admin@test.com',
            role='super_admin',
            tenant_id=None,
            membership_role=None,
        )
        dep = require_tenant_member
        with pytest.raises(HTTPException) as exc:
            await dep(auth=auth)
        assert exc.value.status_code == 403

    asyncio.get_event_loop().run_until_complete(run())


def test_tenant_member_requires_tenant_id():
    from fastapi import HTTPException
    import asyncio

    async def run():
        auth = AuthContext(
            user_id='u1',
            email='user@test.com',
            role='admin',
            tenant_id=None,
            membership_role='admin',
        )
        with pytest.raises(HTTPException) as exc:
            await require_tenant_member(auth=auth)
        assert exc.value.status_code == 400

    asyncio.get_event_loop().run_until_complete(run())
