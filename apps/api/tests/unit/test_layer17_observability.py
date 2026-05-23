"""Layer 17 — observability metrics and tenant scoping."""

from pathlib import Path


def test_observability_metrics_module_exists():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'observability_metrics.py'
    text = path.read_text(encoding='utf-8')
    assert 'set_app_start_time' in text
    assert 'build_tenant_metrics_summary' in text
    assert 'compute_queue_failure_rate' in text
    assert 'canonical_health_path' in text


def test_main_sets_app_start_time():
    path = Path(__file__).resolve().parents[2] / 'src' / 'main.py'
    assert 'set_app_start_time' in path.read_text(encoding='utf-8')


def test_observability_router_uses_metrics_subrouter_and_tenant_guard():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'observability.py'
    text = path.read_text(encoding='utf-8')
    assert 'metrics_router = APIRouter' in text
    assert 'require_tenant_member' in text
    assert 'MOCK_START_TIME' not in text
    assert 'build_tenant_metrics_summary' in text
    assert '_tenant_uuid' in text


def test_tenant_paths_exempt_observability_health():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'tenant_paths.py'
    assert '/api/v1/observability/health' in path.read_text(encoding='utf-8')


def test_fe_observability_hook_paths():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'hooks' / 'use-observability.ts'
    text = path.read_text(encoding='utf-8')
    assert '/api/v1/observability/metrics/summary' in text
    assert '/api/v1/observability/trends' in text
