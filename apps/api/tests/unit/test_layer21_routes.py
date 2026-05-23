"""Layer 21 — UI routes and dead links."""

from pathlib import Path


def test_routes_module_defines_canonical_paths():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'routes.ts'
    text = path.read_text(encoding='utf-8')
    assert 'tenderNew' in text
    assert 'tenderReview' in text
    assert 'reviewLegacy' in text
    assert 'isPublicAppPath' in text


def test_tenders_new_page_exists():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'app' / '(dashboard)' / 'dashboard' / 'tenders' / 'new' / 'page.tsx'
    assert path.is_file()


def test_review_legacy_redirects_to_tender_review():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'app' / '(dashboard)' / 'dashboard' / 'review' / 'page.tsx'
    text = path.read_text(encoding='utf-8')
    assert 'redirect' in text
    assert 'tenderReview' in text or 'tenders/review' in text


def test_admin_sign_in_redirects_to_sign_in():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'app' / 'admin' / 'sign-in' / 'page.tsx'
    text = path.read_text(encoding='utf-8')
    assert 'redirect' in text
    assert 'signIn' in text or '/sign-in' in text


def test_organizations_and_notifications_pages_exist():
    root = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'app' / '(dashboard)' / 'dashboard'
    assert (root / 'organizations' / 'page.tsx').is_file()
    assert (root / 'notifications' / 'page.tsx').is_file()


def test_nav_review_points_to_tender_review():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'design-system' / 'icons.ts'
    assert '/dashboard/tenders/review' in path.read_text(encoding='utf-8')
    assert "'/dashboard/review'" not in path.read_text(encoding='utf-8')


def test_middleware_includes_public_auth_paths():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'middleware.ts'
    text = path.read_text(encoding='utf-8')
    assert '/landing' in text
    assert '/admin/sign-in' in text
    assert '/onboarding' in text
