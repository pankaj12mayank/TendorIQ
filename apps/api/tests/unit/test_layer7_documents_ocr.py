"""Layer L7 — documents, upload & OCR."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / 'apps' / 'web' / 'src'
API = REPO / 'apps' / 'api'


def test_virus_scan_wired_on_upload_routes():
    files_text = (API / 'src' / 'api' / 'routers' / 'files.py').read_text(encoding='utf-8')
    docs_text = (API / 'src' / 'api' / 'routers' / 'documents.py').read_text(encoding='utf-8')
    assert 'assert_upload_clean' in files_text
    assert 'assert_upload_clean' in docs_text
    assert (API / 'src' / 'core' / 'security' / 'upload_scan.py').is_file()


def test_fe_contract_documents_and_ocr_paths():
    import json

    paths = json.loads((API / 'tests' / 'contracts' / 'fe_api_paths.json').read_text(encoding='utf-8'))[
        'paths'
    ]
    for segment in ('/documents/list', '/documents/stats', '/documents/batch', '/documents/retry'):
        assert any(segment in p for p in paths)
    for segment in ('/ocr/process', '/ocr/status', '/ocr/retry'):
        assert any(segment in p for p in paths)


def test_ocr_feature_gate_on_api():
    text = (API / 'src' / 'api' / 'routers' / 'ocr.py').read_text(encoding='utf-8')
    assert 'require_document_ocr_enabled' in text
    assert 'FEATURE_DOCUMENT_OCR' in text


def test_web_ocr_respects_feature_flag():
    text = (WEB / 'hooks' / 'use-ocr.ts').read_text(encoding='utf-8')
    assert "isAppFeatureEnabled('document_ocr')" in text
    text_card = (WEB / 'components' / 'ocr' / 'ocr-status.tsx').read_text(encoding='utf-8')
    assert 'document_ocr' in text_card


def test_polling_errors_friendly_messages():
    text = (WEB / 'hooks' / 'use-documents.ts').read_text(encoding='utf-8')
    assert 'PollingTimeoutError' in text
    assert 'formatPollingError' in text
    ocr = (WEB / 'hooks' / 'use-ocr.ts').read_text(encoding='utf-8')
    assert 'PollingTimeoutError' in ocr


def test_upload_direct_before_presign():
    text = (WEB / 'hooks' / 'use-file-upload.ts').read_text(encoding='utf-8')
    assert '/api/v1/files/upload/direct' in text
    assert '/api/v1/files/upload/initiate' in text


def test_env_example_documents_storage_notes():
    text = (REPO / '.env.example').read_text(encoding='utf-8')
    assert 'upload/direct' in text
    assert 'resolved_storage_local_path' in text or 'apps/api' in text


def test_documents_use_sonner_only():
    docs_page = (WEB / 'app' / '(dashboard)' / 'dashboard' / 'documents' / 'page.tsx').read_text(encoding='utf-8')
    assert "from 'sonner'" in docs_page
    assert 'toast-store' not in docs_page


def test_batch_partial_failure_toast():
    text = (WEB / 'hooks' / 'use-documents.ts').read_text(encoding='utf-8')
    assert 'toast.warning' in text
    assert 'fetchDocuments' in text


def test_playwright_upload_smoke_spec():
    assert (REPO / 'apps' / 'web' / 'e2e' / 'upload-documents.spec.ts').is_file()
