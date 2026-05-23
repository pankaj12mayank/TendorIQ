"""Layer 16 — export API and FE path alignment."""

from pathlib import Path

def test_export_job_response_envelope():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'export.py'
    text = path.read_text(encoding='utf-8')
    assert "def _export_job_response(job)" in text
    assert "'success': True" in text
    assert "'export_id': job.export_id" in text


def test_export_router_has_compat_and_report_routes():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'export.py'
    text = path.read_text(encoding='utf-8')
    assert "from ..dependencies.auth import get_current_user" in text
    assert "@router.post('/export/risk_analysis/{analysis_id}')" in text
    assert "@router.post('/export/report/{tender_id}')" in text
    assert "@router.get('/{export_id}/download')" in text
    assert text.rindex("@router.get('/{export_id}/download')") > text.index("@router.get('/history')")


def test_export_service_inline_source():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'export' / 'service.py'
    text = path.read_text(encoding='utf-8')
    assert 'set_inline_source' in text
    assert '_inline_source.pop' in text


def test_entity_path_segments_documented_in_fe():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'export-api.ts'
    text = path.read_text(encoding='utf-8')
    assert "risk_analysis: 'risk-analysis'" in text
    assert 'export/report/' in text


def test_tenant_org_id_requires_tenant():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'export.py'
    text = path.read_text(encoding='utf-8')
    assert 'def _tenant_org_id' in text
    assert 'Tenant context required for exports' in text
