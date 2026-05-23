"""Layer 27 — Testing & CI gaps."""

from pathlib import Path


def test_conftest_sets_test_env_defaults():
    path = Path(__file__).resolve().parents[1] / 'conftest.py'
    text = path.read_text(encoding='utf-8')
    assert 'DATABASE_URL' in text
    assert 'JWT_SECRET' in text


def test_fe_api_contract_json_exists():
    path = Path(__file__).resolve().parents[1] / 'contracts' / 'fe_api_paths.json'
    text = path.read_text(encoding='utf-8')
    assert '/api/v1/tenders' in text
    assert '/api/v1/auth/me' in text


def test_openapi_contract_module_defers_app_import():
    path = Path(__file__).resolve().parents[1] / 'unit' / 'test_openapi_contract.py'
    text = path.read_text(encoding='utf-8')
    assert 'api_client' in text
    assert 'from src.main import app' in text
    assert text.index('from src.main import app') > text.index('def api_client')


def test_ci_workflow_runs_api_pytest():
    path = Path(__file__).resolve().parents[4] / '.github' / 'workflows' / 'ci.yml'
    text = path.read_text(encoding='utf-8')
    assert 'test-api:' in text
    assert 'pytest tests/unit tests/integration' in text


def test_web_api_contract_vitest_exists():
    path = (
        Path(__file__).resolve().parents[3]
        / 'web'
        / 'src'
        / 'lib'
        / '__tests__'
        / 'api-contract.test.ts'
    )
    text = path.read_text(encoding='utf-8')
    assert 'fe_api_paths.json' in text
    assert 'ROUTES' in text


def test_e2e_public_routes_spec_exists():
    path = Path(__file__).resolve().parents[3] / 'web' / 'e2e' / 'public-routes.spec.ts'
    text = path.read_text(encoding='utf-8')
    assert 'sign-in' in text
    assert 'dashboard' in text


def test_query_error_message_unit_test_exists():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / '__tests__' / 'query-error-message.test.ts'
    assert path.is_file()


def test_organizations_router_syntax_fixed():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'routers' / 'organizations.py'
    text = path.read_text(encoding='utf-8')
    assert '"""Organizations API Router"""' in text.splitlines()[0]
    assert '\\"\\"\\"' not in text
