"""Layer L1 — monorepo & Python dependency alignment."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
API = REPO / 'apps' / 'api'


def test_requirements_dev_includes_runtime_and_pytest():
    text = (API / 'requirements-dev.txt').read_text(encoding='utf-8')
    assert '-r requirements.txt' in text
    assert 'pytest' in text
    assert 'ruff' in text


def test_requirements_txt_has_no_dev_only_ruff():
    text = (API / 'requirements.txt').read_text(encoding='utf-8')
    assert 'pytest' not in text
    assert 'ruff' not in text


def test_root_postinstall_runs_node_script():
    pkg = (REPO / 'package.json').read_text(encoding='utf-8')
    assert 'scripts/postinstall.js' in pkg
    assert 'Skipping postinstall' not in pkg


def test_start_script_uses_requirements_dev():
    start = (REPO / 'scripts' / 'tenderiq-start.ps1').read_text(encoding='utf-8')
    assert 'Install-TenderIqPythonDeps' in start
    assert 'requirements-dev.txt' in start


def test_start_uses_frozen_lockfile_by_default():
    start = (REPO / 'scripts' / 'tenderiq-start.ps1').read_text(encoding='utf-8')
    assert '--frozen-lockfile' in start
    assert '--no-frozen-lockfile' not in start


def test_ci_uses_setup_api_python_action():
    ci = (REPO / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
    assert 'setup-api-python' in ci
    assert 'uv sync' not in ci


def test_composite_action_installs_requirements_dev():
    action = (REPO / '.github' / 'actions' / 'setup-api-python' / 'action.yml').read_text(
        encoding='utf-8'
    )
    assert 'requirements-dev.txt' in action


def test_api_package_json_documents_tooling():
    pkg = (API / 'package.json').read_text(encoding='utf-8')
    assert '"test"' in pkg
    assert 'requirements-dev.txt' in pkg or 'turbo' in pkg


def test_monorepo_doc_python_versions():
    doc = (REPO / 'docs' / 'monorepo-tooling.md').read_text(encoding='utf-8')
    assert '3.12' in doc
    assert 'requirements-dev.txt' in doc


def test_deployment_uses_requirements_txt_no_docker():
    dep = (REPO / 'docs' / 'deployment.md').read_text(encoding='utf-8')
    assert 'requirements.txt' in dep
    assert 'apps/api' in dep
    assert 'docker compose' not in dep.lower()
    assert 'Dockerfile' not in dep
