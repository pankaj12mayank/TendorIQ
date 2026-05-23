"""Layer 18 — enterprise SSO configuration and session exchange."""

from pathlib import Path


def test_sso_router_db_backed_and_rbac():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'sso.py'
    text = path.read_text(encoding='utf-8')
    assert 'save_sso_config' in text
    assert 'load_sso_config' in text
    assert 'RequireOrgUpdate' in text
    assert 'RequireSettingsRead' in text
    assert "role in ['admin'" not in text
    assert 'exchange_sso_session' in text
    assert '/public/config' in text
    assert 'SSOSessionRequest' in text


def test_sso_tenant_store_persists_on_settings():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'sso' / 'tenant_store.py'
    text = path.read_text(encoding='utf-8')
    assert "SSO_SETTINGS_KEY = 'sso'" in text
    assert 'config_to_public' in text
    assert 'get_tenant_by_slug' in text


def test_sso_bootstrap_issues_jwt():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'sso' / 'bootstrap.py'
    text = path.read_text(encoding='utf-8')
    assert 'issue_session_tokens' in text
    assert 'ensure_sso_membership' in text


def test_sso_handler_group_mapping():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'sso' / '__init__.py'
    text = path.read_text(encoding='utf-8')
    assert 'GROUP_TO_MEMBERSHIP' in text
    assert 'permissions_for_role' in text
    assert '_configs' not in text


def test_tenant_paths_exempt_public_sso():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'tenant_paths.py'
    text = path.read_text(encoding='utf-8')
    assert '/api/v1/sso/session' in text
    assert '/api/v1/sso/public/' in text


def test_fe_sso_api_and_hook_paths():
    api = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'sso-api.ts'
    hook = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'hooks' / 'use-sso.ts'
    api_text = api.read_text(encoding='utf-8')
    hook_text = hook.read_text(encoding='utf-8')
    session = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'sso-session.ts'
    session_text = session.read_text(encoding='utf-8')
    assert '/api/v1/sso/public/config' in session_text
    assert '/api/v1/sso/session' in session_text
    assert 'exchangeSsoSession' in session_text
    assert 'parseSsoPublicConfig' in api_text
    assert 'useSsoSignIn' in hook_text
    assert 'useSsoAdmin' in hook_text
