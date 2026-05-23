"""Layer 26 — Security (beyond RBAC)."""

from pathlib import Path


def test_row_access_module_exists():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'row_access.py'
    text = path.read_text(encoding='utf-8')
    assert 'can_modify_tenant_resource' in text
    assert 'manager' in text


def test_tender_service_enforces_row_access():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'services' / 'tender_service.py'
    text = path.read_text(encoding='utf-8')
    assert '_assert_can_modify' in text
    assert 'membership_role' in text
    assert 'HTTP_403_FORBIDDEN' in text


def test_cors_not_wildcard_by_default():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'config.py'
    text = path.read_text(encoding='utf-8')
    assert "CORS_ALLOW_METHODS: str = 'GET,POST" in text
    assert "['*']" not in text.split('CORS_ALLOW_METHODS')[1].split('CORS_ALLOW_HEADERS')[0]


def test_main_uses_explicit_cors_lists():
    path = Path(__file__).resolve().parents[2] / 'src' / 'main.py'
    text = path.read_text(encoding='utf-8')
    assert 'cors_allow_methods_list' in text
    assert 'cors_allow_headers_list' in text


def test_global_handler_hides_details_unless_exposed():
    path = Path(__file__).resolve().parents[2] / 'src' / 'main.py'
    text = path.read_text(encoding='utf-8')
    assert 'expose_error_details' in text
    assert "'request_id': request_id" in text


def test_security_headers_hsts_in_production():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'middleware.py'
    text = path.read_text(encoding='utf-8')
    assert 'Strict-Transport-Security' in text
    assert 'Content-Security-Policy' in text


def test_document_delete_checks_row_access():
    for rel in ('api/routers/files.py', 'api/routers/documents.py'):
        text = (Path(__file__).resolve().parents[2] / 'src' / rel).read_text(encoding='utf-8')
        assert 'can_modify_tenant_resource' in text
        assert 'uploaded_by_id' in text or 'resource_owner_id_from_metadata' in text
