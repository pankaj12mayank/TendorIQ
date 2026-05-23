"""Layer 33 — Audit coverage & export limits."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]


def test_audit_limits_module():
    text = (REPO / 'apps' / 'api' / 'src' / 'core' / 'audit_limits.py').read_text(encoding='utf-8')
    assert 'MAX_AUDIT_EXPORT_ROWS' in text
    assert 'clamp_export_limit' in text


def test_tender_create_update_audit_helpers():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'routers' / 'tenders.py').read_text(encoding='utf-8')
    assert '_audit_tender_mutation' in text
    assert "action='create'" in text
    assert "action='update'" in text
    assert 'logger.warning' in text
    assert 'except Exception:\n        pass' not in text


def test_document_upload_delete_audit():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'routers' / 'documents.py').read_text(encoding='utf-8')
    assert 'tenant_audit.log_create' in text
    assert 'tenant_audit.log_delete' in text
    assert "action_type='upload'" in text


def test_platform_export_caps_rows():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'router' / 'admin_platform.py').read_text(
        encoding='utf-8'
    )
    assert 'clamp_export_limit' in text
    assert '.limit(export_limit)' in text


def test_tenant_export_caps_and_self_logs():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'router' / 'audit.py').read_text(encoding='utf-8')
    assert 'clamp_export_limit' in text
    assert "action_type='export'" in text
    assert '.limit(export_limit)' in text


def test_web_audit_constants():
    text = (REPO / 'apps' / 'web' / 'src' / 'lib' / 'audit-constants.ts').read_text(encoding='utf-8')
    assert 'PLATFORM_AUDIT_LIST_LIMIT' in text
    assert 'PLATFORM_AUDIT_EXPORT_MAX_ROWS' in text


def test_use_admin_uses_audit_constants():
    text = (REPO / 'apps' / 'web' / 'src' / 'hooks' / 'use-admin.ts').read_text(encoding='utf-8')
    assert 'audit-constants' in text
    assert 'limit: PLATFORM_AUDIT_EXPORT_MAX_ROWS' in text


def test_audit_coverage_doc_exists():
    assert (REPO / 'docs' / 'audit-coverage.md').is_file()
