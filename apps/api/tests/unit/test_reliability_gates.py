"""Reliability gates — ensure audit process includes import/compile guards."""

from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[4]
API = REPO / 'apps' / 'api'


def test_verify_import_script_exists():
    assert (API / 'scripts' / 'verify_import.py').is_file()


def test_audit_report_has_root_cause_section():
    text = (REPO / 'AUDIT_REPORT.md').read_text(encoding='utf-8')
    assert 'System reliability & root causes' in text
    assert 'RC-01' in text
    assert 'Reliability gates' in text


def test_audit_methodology_doc_exists():
    assert (REPO / 'docs' / 'audit-methodology.md').is_file()


def test_ci_runs_import_gate():
    text = (REPO / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
    assert 'verify_import.py' in text
    assert 'compileall' in text


def test_api_src_compiles():
    result = subprocess.run(
        [sys.executable, '-m', 'compileall', '-q', 'src'],
        cwd=API,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
