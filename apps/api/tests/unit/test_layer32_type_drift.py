"""Layer 32 — Shared types & FE/API drift."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]


def test_shared_roles_module():
    text = (REPO / 'packages' / 'shared' / 'src' / 'roles.ts').read_text(encoding='utf-8')
    assert 'AdminConsoleRole' in text
    assert "'owner'" in text
    assert "'member'" in text
    assert 'tenant_admin' in text


def test_shared_plans_module():
    text = (REPO / 'packages' / 'shared' / 'src' / 'plans.ts').read_text(encoding='utf-8')
    assert 'normalizePlanId' in text
    assert 'plan_pro' in text
    assert 'professional' in text


def test_shared_notifications_mapper():
    text = (REPO / 'packages' / 'shared' / 'src' / 'notifications.ts').read_text(encoding='utf-8')
    assert 'mapApiNotification' in text
    assert 'action_url' in text


def test_web_notifications_api_reexports_shared():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'notifications-api.ts').read_text(encoding='utf-8')
    assert '@tendoriq/shared/notifications' in text
    assert 'function mapApiNotification' not in text


def test_web_billing_bridge_reexports_shared():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'billing-plan-bridge.ts').read_text(encoding='utf-8')
    assert '@tendoriq/shared/plans' in text


def test_admin_types_use_shared_roles():
    text = (REPO / 'apps' / 'web' / 'src' / 'components' / 'admin' / 'types.ts').read_text(
        encoding='utf-8'
    )
    assert '@tendoriq/shared/roles' in text
    assert "export type UserRole = AdminConsoleRole" in text


def test_auth_session_uses_shared_session_user():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'auth-session.ts').read_text(encoding='utf-8')
    assert '@tendoriq/shared/auth' in text
    assert 'SessionUser' in text


def test_step4_schema_normalizes_plan_aliases():
    text = (REPO / 'packages' / 'shared' / 'src' / 'types' / 'index.ts').read_text(encoding='utf-8')
    assert 'normalizePlanId' in text
    assert 'normalizeBillingCycle' in text


def test_package_exports_type_modules():
    pkg = (REPO / 'packages' / 'shared' / 'package.json').read_text(encoding='utf-8')
    assert './roles' in pkg
    assert './plans' in pkg
    assert './notifications' in pkg
    assert './auth' in pkg


def test_type_drift_doc_exists():
    assert (REPO / 'docs' / 'type-drift.md').is_file()
