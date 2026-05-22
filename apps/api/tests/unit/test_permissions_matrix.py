"""Ensure API RBAC matrix matches packages/shared/permissions.json."""

import json
from pathlib import Path

from src.core.rbac import Permission, ROLE_PERMISSIONS

_MATRIX = Path(__file__).resolve().parents[4] / 'packages' / 'shared' / 'permissions.json'


def test_role_permissions_match_shared_json():
    with _MATRIX.open(encoding='utf-8') as f:
        expected: dict[str, list[str]] = json.load(f)

    assert set(ROLE_PERMISSIONS.keys()) == set(expected.keys())

    for role, perm_strings in expected.items():
        actual = {p.value for p in ROLE_PERMISSIONS[role]}
        assert actual == set(perm_strings), f'Role {role} drift: {actual ^ set(perm_strings)}'


def test_viewer_has_no_analytics():
    viewer = {p.value for p in ROLE_PERMISSIONS['viewer']}
    assert 'analytics:view' not in viewer


def test_permission_alias_resolves():
    from src.core.rbac import RBACService

    assert RBACService.has_permission('manager', 'tender:write')
    assert RBACService.has_permission('viewer', 'tender:read')
