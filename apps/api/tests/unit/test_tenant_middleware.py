"""Layer 8 — tenant path classification and UUID parsing."""

import pytest
from fastapi import HTTPException

from src.core.tenant_paths import (
    is_auth_public_path,
    is_tenant_exempt_path,
    is_tenant_scoped_path,
)
from src.core.tenant_utils import parse_tenant_uuid


def test_auth_public_paths():
    assert is_auth_public_path('/api/v1/auth/login')
    assert is_auth_public_path('/api/v1/auth/me')
    assert not is_auth_public_path('/api/v1/tenders')


def test_tenant_scoped_paths():
    assert is_tenant_scoped_path('/api/v1/tenders')
    assert is_tenant_scoped_path('/api/v1/analysis/')
    assert not is_tenant_scoped_path('/api/v1/onboarding/status')


def test_onboarding_exempt():
    assert is_tenant_exempt_path('/api/v1/onboarding/step')


def test_observability_health_exempt():
    assert is_tenant_exempt_path('/api/v1/observability/health')
    assert is_tenant_exempt_path('/api/v1/observability/health/live')
    assert is_tenant_exempt_path('/api/v1/admin/platform/users')


def test_parse_tenant_uuid_valid():
    tid = '550e8400-e29b-41d4-a716-446655440000'
    assert str(parse_tenant_uuid(tid)) == tid


def test_parse_tenant_uuid_missing_raises_400():
    with pytest.raises(HTTPException) as exc:
        parse_tenant_uuid(None)
    assert exc.value.status_code == 400


def test_parse_tenant_uuid_invalid_raises_400():
    with pytest.raises(HTTPException) as exc:
        parse_tenant_uuid('not-a-uuid')
    assert exc.value.status_code == 400
