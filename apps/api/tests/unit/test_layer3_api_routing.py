"""Layer L3 — API surface & routing."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
API = REPO / 'apps' / 'api'


def test_main_registers_bids_and_webhooks():
    text = (API / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'bids_router' in text
    assert 'webhooks_router' in text
    assert "include_router(bids_router" in text
    assert "include_router(webhooks_router" in text


def test_webhooks_module_has_no_clerk_route():
    text = (API / 'src' / 'api' / 'routers' / 'webhooks.py').read_text(encoding='utf-8')
    assert "@router.post('/clerk')" not in text
    assert 'ensure_clerk_user' not in text
    assert 'STRIPE_WEBHOOK_SECRET' in text


def test_auth_has_clerk_webhook():
    text = (API / 'src' / 'api' / 'routers' / 'auth.py').read_text(encoding='utf-8')
    assert "/clerk/webhook" in text


def test_fe_contract_includes_bids():
    import json

    data = json.loads((API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8'))
    assert '/api/v1/bids' in data['paths']
    assert '/api/v1/webhooks/stripe' in data['paths']


def test_openapi_contract_uses_prefix_match():
    text = (API / 'tests' / 'unit' / 'test_openapi_contract.py').read_text(encoding='utf-8')
    assert '_path_covered' in text
    assert 'undocumented' in text


def test_main_uvicorn_entrypoint():
    text = (API / 'src' / 'main.py').read_text(encoding='utf-8')
    assert "'src.main:app'" in text
    assert "'main:app'" not in text


def test_super_admin_shim_deprecated():
    text = (API / 'src' / 'api' / 'router' / 'super_admin.py').read_text(encoding='utf-8')
    assert 'DEPRECATED' in text or 'deprecated' in text.lower()
    main = (API / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'super_admin' not in main


def test_tenant_paths_lists_bids():
    text = (API / 'src' / 'core' / 'tenant_paths.py').read_text(encoding='utf-8')
    assert '/api/v1/bids' in text


def test_web_api_ts_reexports_client():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'api.ts').read_text(encoding='utf-8')
    assert "from './api-client'" in text
    assert '@deprecated' in text.lower()


def test_bids_router_file_exists():
    assert (API / 'src' / 'api' / 'routers' / 'bids.py').is_file()
