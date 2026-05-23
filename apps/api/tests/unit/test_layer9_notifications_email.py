"""Layer L9 — notifications & email."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web' / 'src'
API = REPO / 'apps' / 'api'


def test_resend_webhook_sync_module():
    text = (API / 'src' / 'core' / 'email' / 'resend_webhook.py').read_text(encoding='utf-8')
    assert 'apply_resend_webhook_event' in text
    assert 'email.delivered' in text
    assert 'opened_at' in text


def test_webhooks_resend_calls_sync():
    text = (API / 'src' / 'api' / 'routers' / 'webhooks.py').read_text(encoding='utf-8')
    assert 'apply_resend_webhook_event' in text
    assert 'async def resend_webhook(request: Request, db: AsyncSession = Depends(get_db))' in text


def test_startup_warns_missing_resend_key():
    text = (API / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'resend_api_key_configured' in text
    assert 'EMAIL_API_KEY/RESEND_API_KEY is empty' in text


def test_fe_contract_email_template_and_queue_paths():
    import json

    paths = json.loads((API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8'))[
        'paths'
    ]
    for segment in (
        '/email/templates',
        '/email/templates/preview',
        '/email/settings/smtp',
        '/email/queue',
        '/webhooks/resend',
    ):
        assert any(segment in p for p in paths)
    hook = (WEB / 'hooks' / 'use-email-system.ts').read_text(encoding='utf-8')
    for action in ('/activate', '/deactivate', '/duplicate', '/retry'):
        assert action in hook


def test_use_email_system_uses_api_client_directly():
    text = (WEB / 'hooks' / 'use-email-system.ts').read_text(encoding='utf-8')
    assert "from '@/lib/api-client'" in text
    assert 'api.get<' in text
    assert 'function useEmailApi' not in text
    assert 'retryQueueItem' in text


def test_email_trigger_paths_module():
    text = (WEB / 'lib' / 'email-trigger-paths.ts').read_text(encoding='utf-8')
    assert 'upload-received' in text
    hook = (WEB / 'hooks' / 'use-notifications.ts').read_text(encoding='utf-8')
    assert 'EMAIL_TRIGGER_PATHS' in hook
    assert 'emailTriggerApiPath' in hook


def test_email_system_docs_migration_and_encryption():
    text = (REPO / 'docs' / 'EMAIL_SYSTEM.md').read_text(encoding='utf-8')
    assert 'alembic upgrade head' in text
    assert 'ENCRYPTION_KEY' in text
    assert 'rotation' in text.lower()


def test_email_worker_docstring_not_arq():
    text = (API / 'src' / 'core' / 'email' / 'workers' / 'email_worker.py').read_text(encoding='utf-8')
    assert 'ARQ' not in text
    assert 'inline' in text.lower()


def test_playwright_auth_password_spec():
    assert (REPO / 'apps' / 'web' / 'e2e' / 'auth-password-reset.spec.ts').is_file()


def test_env_example_documents_resend_key():
    text = (REPO / '.env.example').read_text(encoding='utf-8')
    assert 'EMAIL_API_KEY=' in text
    assert 'RESEND_WEBHOOK_SECRET' in text
