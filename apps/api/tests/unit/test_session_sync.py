"""Layer 9 — session sync and token issuance."""

from src.core.auth import AuthService
from src.core.local_auth import (
    build_me_response,
    issue_session_tokens,
    login_user_payload,
    permissions_for_role,
)
from src.core.auth import AuthContext


def test_issue_session_tokens_single_builder():
    tokens = issue_session_tokens(
        user_id='user-1',
        email='u@test.com',
        role='admin',
        tenant_id='550e8400-e29b-41d4-a716-446655440000',
        membership_role='admin',
    )
    assert tokens['access_token']
    assert tokens['refresh_token']
    assert tokens['expires_in'] > 0
    assert tokens['token_type'] == 'bearer'

    access = AuthService().verify_token(tokens['access_token'])
    refresh = AuthService().verify_token(tokens['refresh_token'])
    assert access is not None
    assert refresh is not None
    assert access.tenant_id == '550e8400-e29b-41d4-a716-446655440000'
    assert refresh.membership_role == 'admin'


def test_login_payload_includes_permissions():
    user = login_user_payload(
        user_id='u1',
        email='a@b.com',
        name='A',
        role='manager',
        membership_role='manager',
        tenant_id='t1',
        is_super_admin=False,
    )
    assert len(user['permissions']) > 0
    assert 'tender:read' in user['permissions']


def test_super_admin_permissions_include_all_wildcard():
    perms = permissions_for_role('super_admin', None)
    assert 'all' in perms
    assert 'tender:read' in perms


def test_build_me_response_matches_login_shape():
    auth = AuthContext(
        user_id='u1',
        email='a@b.com',
        role='admin',
        tenant_id='t1',
        membership_role='admin',
    )
    me = build_me_response(auth, name='Ada', tenant_id='t1', is_super_admin=False)
    assert me['user_id'] == 'u1'
    assert me['permissions']
    assert me['name'] == 'Ada'
    assert me['tenant_id'] == 't1'
