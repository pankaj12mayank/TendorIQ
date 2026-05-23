"""Layer L8 — billing & usage."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web' / 'src'
API = REPO / 'apps' / 'api'


def test_stripe_webhook_sync_module():
    text = (API / 'src' / 'core' / 'billing' / 'stripe_webhook.py').read_text(encoding='utf-8')
    assert 'apply_stripe_webhook_event' in text
    assert 'customer.subscription.updated' in text


def test_webhooks_stripe_calls_sync():
    text = (API / 'src' / 'api' / 'routers' / 'webhooks.py').read_text(encoding='utf-8')
    assert 'apply_stripe_webhook_event' in text
    assert "Depends(get_db)" in text


def test_fe_contract_billing_paths():
    import json

    paths = json.loads((API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8'))[
        'paths'
    ]
    for segment in (
        '/billing/upgrade',
        '/billing/subscription/change',
        '/billing/subscription/cancel',
        '/billing/invoices',
        '/billing/check-limit',
        '/webhooks/stripe',
    ):
        assert any(segment in p for p in paths)


def test_billing_store_ui_only():
    text = (WEB / 'components' / 'billing' / 'store.ts').read_text(encoding='utf-8')
    assert '@/lib/api-client' not in text
    assert 'changePlan' not in text
    assert 'useBillingApi' in (WEB / 'hooks' / 'use-billing.ts').read_text(encoding='utf-8')


def test_billing_page_uses_hook_for_mutations():
    text = (WEB / 'app' / '(dashboard)' / 'dashboard' / 'billing' / 'page.tsx').read_text(encoding='utf-8')
    assert 'useBillingApi' in text
    assert 'initialize' in text


def test_usage_merges_api_feature_names():
    text = (WEB / 'components' / 'usage' / 'constants.ts').read_text(encoding='utf-8')
    assert 'mergeFeatureConfigFromQuotas' in text
    hook = (WEB / 'components' / 'usage' / 'hooks' / 'use-usage.ts').read_text(encoding='utf-8')
    assert 'mergeFeatureConfigFromQuotas' in hook


def test_billing_quota_doc_exists():
    assert (REPO / 'docs' / 'billing-quota.md').is_file()


def test_admin_billing_separate_from_tenant():
    text = (WEB / 'components' / 'admin' / 'modules' / 'billing.tsx').read_text(encoding='utf-8')
    assert 'not tenant' in text.lower() or 'super admin' in text.lower()


def test_playwright_billing_spec():
    assert (REPO / 'apps' / 'web' / 'e2e' / 'billing.spec.ts').is_file()


def test_notifications_quota_query_documented():
    text = (WEB / 'components' / 'usage' / 'hooks' / 'use-usage.ts').read_text(encoding='utf-8')
    assert 'type=quota' in text
    paths = (API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8')
    assert '/api/v1/notifications' in paths
