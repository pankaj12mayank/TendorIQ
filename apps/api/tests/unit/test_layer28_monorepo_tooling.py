"""Layer 28 — Monorepo & tooling."""

from pathlib import Path

# tests/unit -> tests -> api -> apps -> repo root
REPO = Path(__file__).resolve().parents[4]


def test_pnpm_workspace_includes_apps():
    text = (REPO / 'pnpm-workspace.yaml').read_text(encoding='utf-8')
    assert 'apps/*' in text
    assert 'packages/*' in text


def test_api_package_in_workspace():
    pkg = REPO / 'apps' / 'api' / 'package.json'
    data = pkg.read_text(encoding='utf-8')
    assert '@tendoriq/api' in data
    assert 'workspace:*' in data or '@tendoriq/shared' in data


def test_root_scripts_use_scoped_filters():
    text = (REPO / 'package.json').read_text(encoding='utf-8')
    assert '@tendoriq/web' in text
    assert '@tendoriq/api' in text


def test_ci_uses_pnpm_and_scoped_web_filters():
    text = (REPO / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
    assert 'pnpm install --frozen-lockfile' in text
    assert 'pnpm --filter @tendoriq/web' in text
    assert 'run: npm install' not in text


def test_automated_tests_e2e_uses_preview_script():
    text = (REPO / '.github' / 'workflows' / 'automated-tests.yml').read_text(encoding='utf-8')
    assert 'pnpm --filter @tendoriq/web preview' in text
    web_pkg = (REPO / 'apps' / 'web' / 'package.json').read_text(encoding='utf-8')
    assert '"preview"' in web_pkg


def test_production_ready_validates_env_template_not_live_secrets():
    text = (REPO / '.github' / 'workflows' / 'production-ready.yml').read_text(encoding='utf-8')
    assert '.env.example' in text
    assert 'apps/web/.next' in text
    env_block = text.split('Validate environment template', 1)[1].split('security-scan', 1)[0]
    assert 'REDIS_URL' not in env_block


def test_shared_clean_script_is_cross_platform():
    text = (REPO / 'packages' / 'shared' / 'package.json').read_text(encoding='utf-8')
    assert 'rm -rf' not in text
    assert 'node -e' in text


def test_api_railway_nixpacks_deploy_without_docker():
    assert (REPO / 'apps' / 'api' / 'railway.json').is_file()
    railway = (REPO / 'apps' / 'api' / 'railway.json').read_text(encoding='utf-8')
    assert 'NIXPACKS' in railway
    assert not (REPO / 'apps' / 'api' / 'Dockerfile').exists()
    assert not (REPO / 'docker-compose.yml').exists()


def test_monorepo_tooling_doc_exists():
    doc = REPO / 'docs' / 'monorepo-tooling.md'
    text = doc.read_text(encoding='utf-8')
    assert '@tendoriq/web' in text
    assert 'pnpm-workspace.yaml' in text


def test_web_api_shim_reexports_api_client():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'api.ts').read_text(encoding='utf-8')
    assert "from './api-client'" in text
