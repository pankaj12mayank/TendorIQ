"""Layer L6 — tenant dashboard & core features."""

from pathlib import Path
import json

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web' / 'src'
API = REPO / 'apps' / 'api'


def test_bids_router_registered():
    text = (API / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'bids_router' in text
    assert "include_router(bids_router" in text


def test_bids_page_calls_api_v1_bids():
    text = (WEB / 'app' / '(dashboard)' / 'dashboard' / 'bids' / 'page.tsx').read_text(encoding='utf-8')
    assert "'/api/v1/bids'" in text
    assert 'total_bids' in text


def test_use_api_requires_tenant_workspace():
    text = (WEB / 'hooks' / 'use-api.ts').read_text(encoding='utf-8')
    assert 'hasTenantWorkspace' in text
    assert 'TENANT_WORKSPACE_REQUIRED' in text
    assert 'enabled: tenantReady' in text


def test_fe_contract_includes_analysis_and_exports():
    paths = json.loads((API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8'))[
        'paths'
    ]
    assert '/api/v1/analysis/tender' in paths
    assert '/api/v1/review/session' in paths
    assert any('/exports/export' in p for p in paths)
    assert any('/exports/history' in p for p in paths)


def test_super_admin_tenant_view_escape_hatch():
    text = (WEB / 'lib' / 'super-admin-tenant-view.ts').read_text(encoding='utf-8')
    assert 'tenant_view' in text
    text_layout = (WEB / 'app' / '(dashboard)' / 'layout.tsx').read_text(encoding='utf-8')
    assert 'isSuperAdminTenantViewActive' in text_layout


def test_analytics_page_tenant_first_class():
    text = (WEB / 'app' / '(dashboard)' / 'dashboard' / 'analytics' / 'page.tsx').read_text(encoding='utf-8')
    assert 'ROUTES.usage' in text
    assert "router.replace('/dashboard/admin?module=analytics')" in text


def test_settings_hub_not_redirect_only():
    text = (WEB / 'app' / '(dashboard)' / 'dashboard' / 'settings' / 'page.tsx').read_text(encoding='utf-8')
    assert 'SETTINGS_LINKS' in text
    assert 'ROUTES.settingsProfile' in text


def test_analysis_api_path_in_web():
    text = (WEB / 'lib' / 'analysis-api.ts').read_text(encoding='utf-8')
    assert '/api/v1/analysis/tender/' in text


def test_playwright_tenant_core_spec():
    assert (REPO / 'apps' / 'web' / 'e2e' / 'tenant-core.spec.ts').is_file()


def test_use_api_uses_shared_tender_mappers():
    text = (WEB / 'hooks' / 'use-api.ts').read_text(encoding='utf-8')
    assert 'mapTenderFromApi' in text
    assert 'mapTenderToApi' in text
    assert '@tendoriq/shared/tenders' in text
