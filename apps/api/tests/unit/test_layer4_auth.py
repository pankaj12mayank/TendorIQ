"""Layer L4 — authentication (sign-in → session)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
API = REPO / 'apps' / 'api'
WEB = REPO / 'apps' / 'web' / 'src'


def test_middleware_allows_local_session_cookie():
    text = (WEB / 'middleware.ts').read_text(encoding='utf-8')
    assert '__session' in text
    assert 'hasLocalSession' in text


def test_protected_route_redirects_to_sign_in():
    text = (WEB / 'components' / 'auth' / 'protected-route.tsx').read_text(encoding='utf-8')
    assert 'router.replace' in text
    assert 'ROUTES.signIn' in text
    assert 'Authentication Required' not in text


def test_api_client_uses_unauthorized_handler():
    text = (WEB / 'lib' / 'api-client.ts').read_text(encoding='utf-8')
    assert 'notifyUnauthorized' in text
    assert 'window.location.href' not in text


def test_sign_up_clerk_no_force_redirect_onboarding_only():
    text = (WEB / 'app' / '(auth)' / 'sign-up' / 'sign-up-clerk.tsx').read_text(encoding='utf-8')
    assert 'forceRedirectUrl' not in text
    assert 'fallbackRedirectUrl="/onboarding"' in text


def test_guest_route_redirects_away_from_auth_pages():
    text = (WEB / 'components' / 'auth' / 'protected-route.tsx').read_text(encoding='utf-8')
    assert 'isGuestAuthPath' in text
    assert 'getPostLoginPath' in text


def test_svix_support_module():
    text = (API / 'src' / 'core' / 'svix_support.py').read_text(encoding='utf-8')
    assert 'SVIX_AVAILABLE' in text


def test_clerk_webhook_uses_svix_module_not_lazy_import():
    text = (API / 'src' / 'api' / 'routers' / 'auth.py').read_text(encoding='utf-8')
    assert 'from ...core.svix_support import' in text
    assert 'from svix.webhooks import' not in text.split('clerk_webhook', 1)[1][:800]


def test_auth_status_documents_super_admin():
    text = (API / 'src' / 'api' / 'routers' / 'auth.py').read_text(encoding='utf-8')
    assert 'super_admin_note' in text
    assert 'svix_package_available' in text


def test_demo_login_clear_db_error():
    text = (API / 'src' / 'api' / 'routers' / 'auth.py').read_text(encoding='utf-8')
    assert 'alembic upgrade head' in text


def test_routes_include_onboarding_public():
    text = (WEB / 'lib' / 'routes.ts').read_text(encoding='utf-8')
    assert 'ROUTES.onboarding' in text
    assert 'PUBLIC_ROUTE_PREFIXES' in text


def test_resend_webhook_verifies_signature():
    text = (API / 'src' / 'api' / 'routers' / 'webhooks.py').read_text(encoding='utf-8')
    assert '_verify_svix_delivery' in text
    assert 'RESEND_WEBHOOK_SECRET' in text
