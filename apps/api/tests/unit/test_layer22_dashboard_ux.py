"""Layer 22 — dashboard UX and loading states."""

from pathlib import Path


def test_dashboard_layout_onboarding_timeout_and_boot_loading():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'app' / '(dashboard)' / 'layout.tsx'
    text = path.read_text(encoding='utf-8')
    assert 'ONBOARDING_CHECK_TIMEOUT_MS' in text
    assert 'DashboardBootLoading' in text
    assert 'Checking workspace setup' in text
    assert 'SidebarSkeleton' in text


def test_rbac_guards_use_loading_placeholder():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'auth' / 'rbac.tsx'
    text = path.read_text(encoding='utf-8')
    assert 'GuardLoadingPlaceholder' in text
    assert 'return null' not in text or text.count('return null') <= 2


def test_reduced_motion_hook_and_sidebar():
    hook = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'use-reduced-motion.ts'
    sidebar = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'design-system' / 'app-sidebar.tsx'
    assert 'prefers-reduced-motion' in hook.read_text(encoding='utf-8')
    sb = sidebar.read_text(encoding='utf-8')
    assert 'useReducedMotion' in sb
    assert 'sidebarLayoutTransition' in sb


def test_dashboard_loading_components():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'layout' / 'dashboard-loading.tsx'
    text = path.read_text(encoding='utf-8')
    assert 'SidebarSkeleton' in text
    assert 'DashboardBootLoading' in text


def test_dashboard_segment_loading():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'app' / '(dashboard)' / 'loading.tsx'
    assert 'DashboardBootLoading' in path.read_text(encoding='utf-8')


def test_guest_route_redirect_loading():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'auth' / 'protected-route.tsx'
    text = path.read_text(encoding='utf-8')
    assert 'Redirecting' in text
    assert 'isAuthenticated' in text


def test_home_dashboard_table_skeleton():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'app' / '(dashboard)' / 'dashboard' / 'page.tsx'
    assert 'TableRowSkeleton' in path.read_text(encoding='utf-8')
