"""Layer 23 — Admin modules (platform APIs + FE wiring)."""

from pathlib import Path


def test_platform_metrics_exports_queue_and_health_helpers():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'platform_metrics.py'
    text = path.read_text(encoding='utf-8')
    assert 'async def platform_queue_stats' in text
    assert 'async def platform_system_health' in text
    assert "'queueStats'" in text
    assert "'systemHealth'" in text


def test_admin_platform_queue_controls_and_audit_logs():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'admin_platform.py'
    text = path.read_text(encoding='utf-8')
    assert '/queue/jobs/{job_id}/cancel' in text
    assert '/queue/jobs/{job_id}/pause' in text
    assert '/queue/jobs/{job_id}/resume' in text
    assert '/audit-logs' in text
    assert '/health' in text


def test_admin_platform_api_module_exists():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'admin-platform-api.ts'
    text = path.read_text(encoding='utf-8')
    assert 'parsePlatformAnalyticsSummary' in text
    assert 'parsePlatformAuditLogsResponse' in text
    assert 'parsePlatformQueueStats' in text


def test_monitoring_uses_live_props_not_random_interval():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'admin' / 'monitoring.tsx'
    text = path.read_text(encoding='utf-8')
    assert 'stats?: PlatformQueueStats' in text
    assert 'metrics?: RealtimeMetricsData' in text
    assert 'Math.random' not in text
    assert 'setInterval' not in text


def test_use_admin_uses_platform_audit_logs():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'hooks' / 'use-admin.ts'
    text = path.read_text(encoding='utf-8')
    assert '/api/v1/admin/platform/audit-logs' in text
    assert 'parsePlatformUsersResponse' in text
    assert 'parsePlatformQueueJobsResponse' in text


def test_constants_admin_role_options_from_matrix():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'admin' / 'constants.ts'
    text = path.read_text(encoding='utf-8')
    assert 'ADMIN_ROLE_OPTIONS' in text
    assert 'ROLE_PERMISSIONS_MATRIX' in text


def test_admin_page_wires_monitoring_props():
    path = (
        Path(__file__).resolve().parents[3]
        / 'web'
        / 'src'
        / 'app'
        / '(dashboard)'
        / 'dashboard'
        / 'admin'
        / 'page.tsx'
    )
    text = path.read_text(encoding='utf-8')
    assert 'queueStats' in text
    assert 'systemHealth' in text
    assert 'SystemHealth' in text
