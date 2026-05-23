"""Row-level access policy tests."""

import os

os.environ.setdefault(
    'DATABASE_URL',
    'mysql+aiomysql://root:pass@localhost:3306/tendoriq?charset=utf8mb4',
)
os.environ.setdefault('JWT_SECRET', 'test-secret-key-at-least-32-chars-long')

from src.core.row_access import can_modify_tenant_resource, resource_owner_id_from_metadata


def test_manager_can_modify_any_tender():
    assert can_modify_tenant_resource(
        user_id='user-a',
        membership_role='manager',
        created_by_id='user-b',
    )


def test_member_only_own_tender():
    assert can_modify_tenant_resource(
        user_id='user-a',
        membership_role='member',
        created_by_id='user-a',
    )
    assert not can_modify_tenant_resource(
        user_id='user-a',
        membership_role='member',
        created_by_id='user-b',
    )


def test_owner_from_metadata():
    assert resource_owner_id_from_metadata({'uploaded_by_id': 'abc'}) == 'abc'
