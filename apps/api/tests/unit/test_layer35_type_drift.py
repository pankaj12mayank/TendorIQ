"""Layer 35 — Remaining FE/API type drift (analysis + tenant IDs)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]


def test_shared_analysis_module():
    text = (REPO / 'packages' / 'shared' / 'src' / 'analysis.ts').read_text(encoding='utf-8')
    assert 'parseAnalysisDashboard' in text
    assert 'analysisDashboardSchema' in text
    assert '.passthrough()' in text


def test_web_analysis_mapper():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'analysis-mapper.ts').read_text(encoding='utf-8')
    assert 'mapAnalysisDashboardToUi' in text
    assert 'keyFindings' in text
    assert 'keyHighlights' in text


def test_use_analysis_uses_shared_parse_and_mapper():
    text = (REPO / 'apps' / 'web' / 'src' / 'hooks' / 'use-analysis.ts').read_text(encoding='utf-8')
    assert '@tendoriq/shared/analysis' in text
    assert 'mapAnalysisDashboardToUi' in text
    assert 'analysisSchema' not in text


def test_use_api_imports_tenders_from_shared():
    text = (REPO / 'apps' / 'web' / 'src' / 'hooks' / 'use-api.ts').read_text(encoding='utf-8')
    assert '@tendoriq/shared/tenders' in text
    assert "export type Tender = ClientTender" in text


def test_tenant_types_module():
    text = (REPO / 'apps' / 'api' / 'src' / 'core' / 'tenant_types.py').read_text(encoding='utf-8')
    assert 'TenantId' in text
    assert 'parse_tenant_uuid' in text


def test_rbac_deps_validates_tenant_uuid():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'dependencies' / 'rbac_deps.py').read_text(
        encoding='utf-8'
    )
    assert 'parse_tenant_uuid' in text


def test_analysis_dashboard_api_shape_documented():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'router' / 'analysis_dashboard.py').read_text(
        encoding='utf-8'
    )
    assert 'keyFindings' in text
    assert 'mandatoryDocs' in text


def test_package_exports_analysis():
    pkg = (REPO / 'packages' / 'shared' / 'package.json').read_text(encoding='utf-8')
    assert './analysis' in pkg
