"""Layer L12 — automated tests & client-ready sign-off."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web'
API = REPO / 'apps' / 'api'


def test_authenticated_e2e_setup_and_flows_exist():
    assert (WEB / 'e2e' / 'auth-demo.setup.ts').is_file()
    assert (WEB / 'e2e' / 'auth-admin.setup.ts').is_file()
    assert (WEB / 'e2e' / 'authenticated-flows.spec.ts').is_file()
    assert (WEB / 'e2e' / 'helpers' / 'auth.ts').is_file()
    config = (WEB / 'playwright.config.ts').read_text(encoding='utf-8')
    assert 'setup-demo' in config
    assert 'chromium-authenticated' in config


def test_client_ready_doc_exists():
    text = (REPO / 'docs' / 'CLIENT_READY.md').read_text(encoding='utf-8')
    assert 'run.bat check' in text
    assert 'run.bat gates' in text
    assert 'Manual smoke' in text


def test_tenderiq_check_runs_layer_tests():
    text = (REPO / 'scripts' / 'tenderiq-check.ps1').read_text(encoding='utf-8')
    assert 'test_layer12_client_ready.py' in text
    assert 'test_layer13_ui_api_disconnect.py' in text
    assert 'auth-unauthorized.test.ts' in text


def test_ci_test_api_has_mysql_and_alembic():
    ci = (REPO / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
    block = ci.split('test-api:', 1)[1].split('test:', 1)[0]
    assert 'mysql:8' in block
    assert 'alembic upgrade head' in block


def test_conftest_disables_rate_limit_noise():
    text = (API / 'tests' / 'conftest.py').read_text(encoding='utf-8')
    assert "RATE_LIMIT_ENABLED', 'false'" in text or 'RATE_LIMIT_ENABLED", "false"' in text


def test_health_readiness_allows_503_without_db():
    unit = (API / 'tests' / 'unit' / 'test_health.py').read_text(encoding='utf-8')
    assert '503' in unit
    assert 'database' in unit


def test_auth_unauthorized_vitest_exists():
    assert (WEB / 'src' / 'lib' / '__tests__' / 'auth-unauthorized.test.ts').is_file()


def test_run_bat_e2e_entry():
    text = (REPO / 'run.bat').read_text(encoding='utf-8')
    assert 'e2e' in text.lower()
    assert 'gates' in text.lower()


def test_gates_script_and_smoke_gate():
    gates = (REPO / 'scripts' / 'tenderiq-gates.ps1').read_text(encoding='utf-8')
    assert 'G0' in gates and 'G5' in gates
    assert 'smoke_gate.py' in gates
    assert (API / 'scripts' / 'smoke_gate.py').is_file()


def test_testing_doc_mentions_authenticated_e2e():
    text = (REPO / 'docs' / 'testing.md').read_text(encoding='utf-8')
    assert 'authenticated' in text.lower() or 'run.bat e2e' in text


def test_e2e_script_exists():
    assert (REPO / 'scripts' / 'tenderiq-e2e.ps1').is_file()
