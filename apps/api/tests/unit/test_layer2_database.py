"""Layer L2 — database & schema lifecycle."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
API = REPO / 'apps' / 'api'


def test_bootstrap_runs_alembic_upgrade():
    text = (REPO / 'scripts' / 'tenderiq-bootstrap.ps1').read_text(encoding='utf-8')
    assert 'alembic upgrade head' in text
    assert 'Initialize-TenderIqDatabase' in text


def test_init_db_fails_without_allow_flag():
    text = (API / 'src' / 'core' / 'database.py').read_text(encoding='utf-8')
    assert 'ALLOW_START_WITHOUT_DB' in text
    assert 'RuntimeError' in text
    assert 'continuing without persistence' not in text


def test_three_alembic_revisions():
    versions = list((API / 'alembic' / 'versions').glob('*.py'))
    names = [p.name for p in versions if not p.name.startswith('__')]
    assert len(names) >= 3
    assert any('layer2_email_audit' in n for n in names)


def test_admin_platform_no_json_dismissed_fallback():
    text = (API / 'src' / 'api' / 'router' / 'admin_platform.py').read_text(encoding='utf-8')
    assert 'list_dismissed_failed_jobs()' not in text
    assert '_DISMISSED_FILE' not in text
    assert 'list_dismissed_failed_jobs_db' in text


def test_railway_config_uses_tenderiq_database():
    text = (REPO / 'apps' / 'api' / 'railway.json').read_text(encoding='utf-8')
    assert 'uvicorn src.main:app' in text
    assert 'requirements.txt' in text
    assert not (REPO / 'docker-compose.yml').exists()


def test_ci_test_api_has_mysql_service():
    ci = (REPO / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
    block = ci.split('test-api:', 1)[1].split('test:', 1)[0]
    assert 'services:' in block
    assert 'mysql:8' in block
    assert 'alembic upgrade head' in block


def test_health_tests_expect_healthy():
    unit = (API / 'tests' / 'unit' / 'test_health.py').read_text(encoding='utf-8')
    integration = (API / 'tests' / 'integration' / 'test_health.py').read_text(encoding='utf-8')
    assert '"healthy"' in unit or "'healthy'" in unit
    assert 'healthy' in integration


def test_readiness_route_exists():
    text = (API / 'src' / 'api' / 'base.py').read_text(encoding='utf-8')
    assert '/health/ready' in text
    assert 'database' in text


def test_start_script_gates_on_readiness():
    text = (REPO / 'scripts' / 'tenderiq-start.ps1').read_text(encoding='utf-8')
    assert 'Test-TenderIqApiReady' in text


def test_email_seed_raises_without_allow_offline():
    text = (API / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'seed_email_system' in text
    assert 'ALLOW_START_WITHOUT_DB' in text
    assert 'RuntimeError' in text
