"""Layer 19 — API response envelope and pagination consistency."""

from pathlib import Path


def test_base_schema_has_paginated_helper():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'schemas' / 'base.py'
    text = path.read_text(encoding='utf-8')
    assert 'def create_paginated_response' in text
    assert 'def create_error_response' in text


def test_notifications_use_meta_pagination():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'notifications.py'
    text = path.read_text(encoding='utf-8')
    assert 'create_paginated_response' in text
    assert "'total': total, 'page': page" not in text


def test_analysis_list_uses_meta_pagination():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'analysis.py'
    text = path.read_text(encoding='utf-8')
    assert 'create_paginated_response' in text
    assert 'create_response' in text
    assert "'total': total, 'page': page" not in text


def test_billing_read_endpoints_use_create_response():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'billing.py'
    text = path.read_text(encoding='utf-8')
    assert 'create_response(await build_subscription_view' in text
    assert 'create_response(await build_usage_summary' in text
    assert "body['plans'] = plans" in text


def test_main_http_exception_returns_error_envelope():
    path = Path(__file__).resolve().parents[2] / 'src' / 'main.py'
    text = path.read_text(encoding='utf-8')
    assert 'http_exception_handler' in text
    assert 'create_error_response' in text


def test_fe_api_envelope_legacy_pagination_and_errors():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'api-envelope.ts'
    text = path.read_text(encoding='utf-8')
    assert 'parseApiErrorMessage' in text
    assert 'legacy?.page' in text
    assert 'parseApiErrorCode' in text


def test_fe_api_client_uses_parseApiErrorMessage():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'api-client.ts'
    assert 'parseApiErrorMessage' in path.read_text(encoding='utf-8')
