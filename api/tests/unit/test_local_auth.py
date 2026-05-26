"""Layer 6 — local JWT auth contract tests."""

from src.core.auth import AuthService
from src.core.local_auth import issue_access_token, login_user_payload


def test_login_payload_includes_id_and_tenant_for_demo_shape():
    user = login_user_payload(
        user_id='uuid-1',
        email='demo@test.com',
        name='Demo',
        role='admin',
        membership_role='admin',
        tenant_id='tenant-uuid',
        is_super_admin=False,
    )
    assert user['id'] == 'uuid-1'
    assert user['user_id'] == 'uuid-1'
    assert user['tenant_id'] == 'tenant-uuid'
    assert user['membership_role'] == 'admin'
    assert 'tender:read' in user['permissions']


def test_super_admin_login_payload_has_no_tenant():
    user = login_user_payload(
        user_id='super_admin',
        email='admin@test.com',
        name='Super Admin',
        role='super_admin',
        membership_role=None,
        tenant_id=None,
        is_super_admin=True,
    )
    assert user['tenant_id'] is None
    assert user['is_super_admin'] is True


def test_demo_jwt_includes_tenant_id():
    service = AuthService()
    service.access_token_expire = 30
    token, _ = service.create_access_token(
        user_id='user-1',
        email='demo@test.com',
        role='admin',
        tenant_id='tenant-abc',
        membership_role='admin',
    )
    payload = service.verify_token(token)
    assert payload is not None
    assert payload.tenant_id == 'tenant-abc'
    assert payload.membership_role == 'admin'


def test_issue_access_token_helper():
    token = issue_access_token(
        user_id='user-1',
        email='demo@test.com',
        role='admin',
        tenant_id='tenant-abc',
        membership_role='admin',
    )
    payload = AuthService().verify_token(token)
    assert payload is not None
    assert payload.tenant_id == 'tenant-abc'


def test_logout_revokes_token_jti():
    service = AuthService()
    service.access_token_expire = 30
    token, _ = service.create_access_token(
        user_id='u1',
        email='u@test.com',
        role='admin',
        tenant_id='t1',
        membership_role='admin',
    )
    first = service.verify_token(token)
    assert first is not None
    service.revoke_token(first.jti)
    assert service.verify_token(token) is None
