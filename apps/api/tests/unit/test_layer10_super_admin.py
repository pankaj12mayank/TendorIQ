"""Layer L10 — super admin & platform console."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web' / 'src'
API = REPO / 'apps' / 'api'


def test_fe_contract_admin_platform_paths():
    import json

    paths = json.loads((API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8'))[
        'paths'
    ]
    for segment in (
        '/admin/platform/billing',
        '/admin/platform/ai-providers',
        '/admin/platform/queue/jobs',
        '/admin/platform/audit-logs/export',
        '/admin/platform/health',
        '/prompts',
    ):
        assert any(segment in p for p in paths)
    paths_ts = (WEB / 'lib' / 'admin-platform-paths.ts').read_text(encoding='utf-8')
    assert 'aiProviderTest' in paths_ts
    assert 'queueJobRetry' in paths_ts


def test_admin_hooks_split_by_domain():
    index = (WEB / 'hooks' / 'admin' / 'index.ts').read_text(encoding='utf-8')
    assert 'useAdminUsersApi' in index
    assert 'useQueueApi' in index
    barrel = (WEB / 'hooks' / 'use-admin.ts').read_text(encoding='utf-8')
    assert "from './admin'" in barrel
    assert 'function useAdminUsersApi' not in (WEB / 'hooks' / 'use-admin.ts').read_text(encoding='utf-8')


def test_admin_platform_paths_module():
    text = (WEB / 'lib' / 'admin-platform-paths.ts').read_text(encoding='utf-8')
    assert 'ADMIN_PLATFORM_PATHS' in text
    assert 'auditLogsExport' in text


def test_admin_api_errors_do_not_throw():
    text = (WEB / 'hooks' / 'admin' / 'admin-api-errors.ts').read_text(encoding='utf-8')
    assert 'reportAdminApiError' in text
    users = (WEB / 'hooks' / 'admin' / 'use-admin-users.ts').read_text(encoding='utf-8')
    assert 'reportAdminApiError' in users
    assert 'throw err' not in users


def test_ai_provider_test_skips_external_without_key():
    text = (API / 'src' / 'api' / 'router' / 'admin_platform.py').read_text(encoding='utf-8')
    block = text.split('async def test_ai_provider', 1)[1].split('@router', 1)[0]
    assert 'dry_run' in block
    assert 'get_provider_secret_db' in block
    assert 'live probe skipped' in block


def test_failed_jobs_dismiss_uses_db_only():
    text = (API / 'src' / 'api' / 'router' / 'admin_platform.py').read_text(encoding='utf-8')
    assert 'dismiss_failed_job_db' in text
    assert 'dismiss_failed_job(' not in text.replace('dismiss_failed_job_db', '')


def test_admin_login_redirects_to_sign_in():
    text = (WEB / 'app' / 'admin' / 'login' / 'page.tsx').read_text(encoding='utf-8')
    assert 'ROUTES.signIn' in text
    assert 'redirect' in text


def test_super_admin_doc_exists():
    assert (REPO / 'docs' / 'super-admin-console.md').is_file()
    text = (REPO / 'docs' / 'super-admin-console.md').read_text(encoding='utf-8')
    assert '/dashboard/admin' in text
    assert 'FEATURE_SSO' in text


def test_platform_analytics_not_tenant_usage():
    text = (WEB / 'hooks' / 'use-analytics.ts').read_text(encoding='utf-8')
    assert 'Platform-wide analytics' in text or 'Platform-wide' in text
    assert 'ADMIN_PLATFORM_PATHS' in text
    module = (WEB / 'components' / 'admin' / 'modules' / 'usage-analytics.tsx').read_text(encoding='utf-8')
    assert 'all tenants' in module.lower()


def test_audit_module_uses_platform_export():
    text = (WEB / 'components' / 'admin' / 'modules' / 'audit-logs.tsx').read_text(encoding='utf-8')
    assert 'useAuditLogApi' in text
    hook = (WEB / 'hooks' / 'admin' / 'use-admin-audit.ts').read_text(encoding='utf-8')
    assert 'auditLogsExport' in hook


def test_playwright_super_admin_and_queue_specs():
    assert (REPO / 'apps' / 'web' / 'e2e' / 'super-admin.spec.ts').is_file()
    text = (REPO / 'apps' / 'web' / 'e2e' / 'super-admin.spec.ts').read_text(encoding='utf-8')
    assert 'module=queue' in text
