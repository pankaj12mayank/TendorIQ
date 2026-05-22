"""Layer 12 — documents & OCR route contracts."""

from pathlib import Path


def test_documents_routes_static_paths_before_dynamic_id():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'routers' / 'documents.py'
    text = path.read_text(encoding='utf-8')
    download_idx = text.find("@router.get('/download/{document_id}')")
    folders_idx = text.find("@router.get('/folders/list')")
    dynamic_idx = text.find("@router.get('/{document_id}')")
    assert download_idx != -1 and folders_idx != -1 and dynamic_idx != -1
    assert download_idx < dynamic_idx
    assert folders_idx < dynamic_idx
    assert text.count("@router.get('/download/{document_id}')") == 1
    assert text.count("@router.get('/folders/list')") == 1


def test_documents_imports_document_model():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'routers' / 'documents.py'
    text = path.read_text(encoding='utf-8')
    assert 'from ...core.models import Document' in text


def test_files_router_uses_get_db_dependency():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'routers' / 'files.py'
    text = path.read_text(encoding='utf-8')
    assert 'AsyncSession = Depends(get_db)' in text
    assert 'db,\n):' not in text


def test_ocr_process_accepts_body_language():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'routers' / 'ocr.py'
    text = path.read_text(encoding='utf-8')
    assert 'Body(None)' in text
    assert 'require_tenant_member' in text
