"""Layer 29 — Enterprise email system (queue, reset flow, contracts)."""

from pathlib import Path

from src.core.email.services.dispatcher import EmailDispatcher
from src.core.email.services.password_reset import PasswordResetService
from src.core.passwords import hash_password, verify_password


REPO = Path(__file__).resolve().parents[4]


def test_password_hash_roundtrip():
    hashed = hash_password('Str0ng-Pass!')
    assert verify_password('Str0ng-Pass!', hashed)
    assert not verify_password('wrong', hashed)


def test_dispatcher_uses_inline_email_process():
    text = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'email' / 'services' / 'dispatcher.py'
    content = text.read_text(encoding='utf-8')
    assert "schedule_job(\n            'email_process'" in content
    assert 'arq' not in content.lower()


def test_reset_password_endpoint_applies_password_before_consume():
    path = REPO / 'apps' / 'api' / 'src' / 'api' / 'router' / 'email_system.py'
    text = path.read_text(encoding='utf-8')
    block = text.split('async def reset_password', 1)[1].split('@router', 1)[0]
    assert 'apply_new_password' in block
    assert block.index('apply_new_password') < block.index('consume_token')


def test_password_reset_service_has_apply_new_password():
    assert hasattr(PasswordResetService, 'apply_new_password')


def test_auth_login_verifies_stored_password_hash():
    path = REPO / 'apps' / 'api' / 'src' / 'api' / 'routers' / 'auth.py'
    text = path.read_text(encoding='utf-8')
    assert 'verify_password' in text
    assert "preferences or {}).get('password_hash')" in text


def test_email_system_router_mounted():
    text = (REPO / 'apps' / 'api' / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'email_system_router' in text
    assert "prefix='/api/v1'" in text or "prefix=\"/api/v1\"" in text


def test_fe_contract_includes_email_system_paths():
    import json

    data = json.loads((REPO / 'apps' / 'api' / 'tests' / 'contracts' / 'fe_api_paths.json').read_text())
    paths = data['paths']
    assert '/api/v1/email/auth/forgot-password' in paths
    assert '/api/v1/email/templates' in paths


def test_email_system_docs_describe_inline_queue():
    text = (REPO / 'docs' / 'EMAIL_SYSTEM.md').read_text(encoding='utf-8')
    assert 'inline' in text.lower()
    assert 'run_worker.py' not in text


def test_env_example_documents_encryption_key():
    text = (REPO / '.env.example').read_text(encoding='utf-8')
    assert 'ENCRYPTION_KEY=' in text


def test_sign_in_links_to_forgot_password():
    text = (REPO / 'apps' / 'web' / 'src' / 'app' / '(auth)' / 'sign-in' / 'page.tsx').read_text(
        encoding='utf-8'
    )
    assert '/forgot-password' in text
