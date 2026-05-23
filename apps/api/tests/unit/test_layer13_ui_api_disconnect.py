"""Layer L13 — UI ↔ API disconnect (real data, no fake timers)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web' / 'src'
API = REPO / 'apps' / 'api'


def test_review_page_uses_tender_id_and_refetch():
    text = (WEB / 'app' / '(dashboard)' / 'dashboard' / 'tenders' / 'review' / 'page.tsx').read_text(
        encoding='utf-8'
    )
    assert "searchParams.get('tenderId')" in text
    assert 'useReviewApi(tenderId)' in text
    assert 'refetch()' in text


def test_review_hook_uses_load_review_session():
    text = (WEB / 'hooks' / 'use-review.ts').read_text(encoding='utf-8')
    assert 'loadReviewSession' in text
    assert '/request-changes' not in text
    assert '/comments' in text or "action: 'request_changes'" in text


def test_review_api_mapper_exists():
    assert (WEB / 'lib' / 'review-api.ts').is_file()
    text = (WEB / 'lib' / 'review-api.ts').read_text(encoding='utf-8')
    assert 'mapReviewSessionFromApi' in text
    assert 'section_statuses' in text


def test_review_store_no_fake_settimeout_approval():
    text = (WEB / 'components' / 'review' / 'store.ts').read_text(encoding='utf-8')
    assert 'submitApproval' not in text
    assert 'setTimeout' not in text


def test_approval_workflow_uses_hook_not_store_fake():
    text = (WEB / 'components' / 'review' / 'sections' / 'approval-workflow.tsx').read_text(
        encoding='utf-8'
    )
    assert 'useApprovalWorkflow' in text


def test_usage_realtime_polls_billing_not_random():
    text = (WEB / 'components' / 'usage' / 'hooks' / 'use-usage.ts').read_text(encoding='utf-8')
    assert 'Math.random' not in text
    assert 'fetchQuotas' in text
    assert '60_000' in text


def test_usage_store_refresh_not_delay_only():
    text = (WEB / 'components' / 'usage' / 'store.ts').read_text(encoding='utf-8')
    assert 'setTimeout(resolve, 800)' not in text


def test_quota_overrides_route_on_api():
    text = (API / 'src' / 'api' / 'router' / 'admin_platform.py').read_text(encoding='utf-8')
    assert '/quota-overrides' in text


def test_regenerate_uses_api_in_hook():
    text = (WEB / 'hooks' / 'use-review.ts').read_text(encoding='utf-8')
    assert '/regenerate' in text
    assert 'include_changes' in text


def test_playwright_review_route_spec():
    assert (REPO / 'apps' / 'web' / 'e2e' / 'review-session.spec.ts').is_file()
