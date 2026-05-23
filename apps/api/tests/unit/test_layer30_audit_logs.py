"""Layer 30 — Audit logs (tenant + platform)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]


def test_audit_present_module():
    path = REPO / 'apps' / 'api' / 'src' / 'core' / 'audit_present.py'
    text = path.read_text(encoding='utf-8')
    assert 'audit_log_to_dict' in text
    assert 'audit_export_payload' in text


def test_tenant_audit_routes_require_analytics_view():
    path = REPO / 'apps' / 'api' / 'src' / 'api' / 'router' / 'audit.py'
    text = path.read_text(encoding='utf-8')
    assert 'RequireAnalyticsView' in text
    assert 'load_users_by_id' in text


def test_platform_audit_logs_total_count_and_export():
    path = REPO / 'apps' / 'api' / 'src' / 'api' / 'router' / 'admin_platform.py'
    text = path.read_text(encoding='utf-8')
    assert "func.count(AuditLog.id)" in text
    assert '/audit-logs/export' in text
    assert "'total': total" in text


def test_audit_logger_default_action_type():
    path = REPO / 'apps' / 'api' / 'src' / 'api' / 'dependencies' / 'audit.py'
    text = path.read_text(encoding='utf-8')
    assert "action_type: str = 'admin_action'" in text


def test_safe_access_denied_log_includes_action_type():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'dependencies' / 'audit.py').read_text(
        encoding='utf-8'
    )
    assert "action_type='admin_action'" in text


def test_login_records_audit_for_tenant_users():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'routers' / 'auth.py').read_text(encoding='utf-8')
    assert '_audit_tenant_login' in text
    assert "action_type='auth'" in text


def test_tender_delete_writes_audit():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'routers' / 'tenders.py').read_text(encoding='utf-8')
    assert 'tenant_audit.log_delete' in text


def test_admin_export_uses_platform_path():
    text = (REPO / 'apps' / 'web' / 'src' / 'hooks' / 'use-admin.ts').read_text(encoding='utf-8')
    assert '/api/v1/admin/platform/audit-logs/export' in text


def test_map_audit_log_includes_state_fields():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'admin-platform-api.ts').read_text(encoding='utf-8')
    assert 'previousState' in text
    assert 'newState' in text


def test_audit_logs_component_hooks_before_return():
    text = (REPO / 'apps' / 'web' / 'src' / 'components' / 'admin' / 'modules' / 'audit-logs.tsx').read_text(
        encoding='utf-8'
    )
    hooks_idx = text.index('useState')
    return_idx = text.index('if (isLoading && logs.length === 0)')
    assert hooks_idx < return_idx
