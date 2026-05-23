"""Layer L5 — onboarding (tenant provisioning)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web' / 'src'
API = REPO / 'apps' / 'api'


def test_dashboard_layout_fail_closed_on_onboarding_error():
    text = (WEB / 'app' / '(dashboard)' / 'layout.tsx').read_text(encoding='utf-8')
    assert 'Fail open' not in text
    assert 'fetchOnboardingStatusAuthenticated' in text
    assert "router.replace('/onboarding')" in text
    assert 'setCheckedOnboarding(true)' in text
    assert 'ONBOARDING_CHECK_TIMEOUT_MS' in text
    # Timeout must not mark complete without is_completed
    assert 'setTimeout(() => {\n      if (!cancelled) setCheckedOnboarding(true)' not in text


def test_dashboard_super_admin_skips_onboarding_check():
    text = (WEB / 'app' / '(dashboard)' / 'layout.tsx').read_text(encoding='utf-8')
    assert "user?.role === 'super_admin'" in text


def test_onboarding_api_shared_status_fetch():
    text = (WEB / 'lib' / 'onboarding-api.ts').read_text(encoding='utf-8')
    assert 'fetchOnboardingStatusAuthenticated' in text
    assert 'shouldCompleteOnboardingFirst' in text


def test_sign_in_clerk_uses_onboarding_api_helper():
    text = (WEB / 'app' / '(auth)' / 'sign-in' / 'sign-in-clerk.tsx').read_text(encoding='utf-8')
    assert 'fetchOnboardingStatusAuthenticated' in text
    assert 'shouldCompleteOnboardingFirst' in text
    assert "fetch(resolveApiUrl('/api/v1/onboarding/status')" not in text


def test_fe_contract_lists_onboarding_steps_and_plans():
    import json

    paths = json.loads((API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8'))[
        'paths'
    ]
    for segment in ('/step/1', '/step/5', '/plans', '/expertise-categories'):
        assert any(segment in p for p in paths)


def test_plan_ids_aligned_shared_and_api_schema():
    shared = (REPO / 'packages' / 'shared' / 'src' / 'plans.ts').read_text(encoding='utf-8')
    schema = (API / 'src' / 'api' / 'schemas' / 'onboarding.py').read_text(encoding='utf-8')
    assert 'professional' in shared
    assert 'free|starter|professional|enterprise' in schema


def test_onboarding_step_error_recovery_banner():
    text = (WEB / 'components' / 'onboarding' / 'step-error-banner.tsx').read_text(encoding='utf-8')
    assert 'Reload progress from server' in text


def test_use_onboarding_step_failure_messages():
    text = (WEB / 'hooks' / 'use-onboarding.ts').read_text(encoding='utf-8')
    assert 'stepFailureMessage' in text
    assert 'failedStep' in text


def test_routes_public_includes_onboarding():
    text = (WEB / 'lib' / 'routes.ts').read_text(encoding='utf-8')
    assert 'ROUTES.onboarding' in text
    assert 'PUBLIC_ROUTE_PREFIXES' in text


def test_playwright_onboarding_spec_exists():
    assert (REPO / 'apps' / 'web' / 'e2e' / 'onboarding.spec.ts').is_file()
