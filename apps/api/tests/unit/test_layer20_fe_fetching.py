"""Layer 20 — frontend data fetching consistency."""

from pathlib import Path


def test_api_config_centralizes_base_url_and_timeouts():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'api-config.ts'
    text = path.read_text(encoding='utf-8')
    assert 'getApiBaseUrl' in text
    assert 'UPLOAD_API_TIMEOUT_MS' in text
    assert 'DEFAULT_API_TIMEOUT_MS' in text


def test_authenticated_fetch_module_exists():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'api-fetch.ts'
    text = path.read_text(encoding='utf-8')
    assert 'authenticatedFetch' in text
    assert 'getSessionRequestHeaders' in text


def test_analysis_store_no_relative_fetch():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'analysis' / 'store.ts'
    text = path.read_text(encoding='utf-8')
    assert "fetch('/api/v1" not in text
    assert 'fetchTenderAnalysis' in text


def test_analysis_api_uses_api_client():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'analysis-api.ts'
    text = path.read_text(encoding='utf-8')
    assert '/api/v1/analysis/tender/' in text
    assert "from './api-client'" in text


def test_file_upload_uses_authenticated_fetch_and_upload_timeout():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'hooks' / 'use-file-upload.ts'
    text = path.read_text(encoding='utf-8')
    assert 'authenticatedFetch' in text
    assert 'UPLOAD_API_TIMEOUT_MS' in text
    assert 'localhost:8000' not in text


def test_export_download_uses_authenticated_fetch():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'export.ts'
    text = path.read_text(encoding='utf-8')
    assert 'authenticatedFetch' in text
    assert 'NEXT_PUBLIC_API_URL' not in text


def test_use_api_exposes_query_error_helper():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'hooks' / 'use-api.ts'
    text = path.read_text(encoding='utf-8')
    assert 'getQueryErrorMessage' in text
    assert 'errorMessage' in text
    assert 'retry: 1' in text
