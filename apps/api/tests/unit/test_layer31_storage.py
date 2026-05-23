"""Layer 31 — File storage (local + async S3)."""

from pathlib import Path

import pytest

from src.core.storage.client import StorageService
from src.core.storage.keys import assert_tenant_storage_key
from src.core.storage.tokens import create_storage_token, verify_storage_token

REPO = Path(__file__).resolve().parents[4]


def test_storage_client_uses_to_thread_for_s3():
    text = (REPO / 'apps' / 'api' / 'src' / 'core' / 'storage' / 'client.py').read_text(
        encoding='utf-8'
    )
    assert 'asyncio.to_thread' in text
    assert 'def read_file' in text


def test_assert_tenant_storage_key_rejects_traversal():
    with pytest.raises(ValueError):
        assert_tenant_storage_key('tenant-1/../../etc/passwd', 'tenant-1')
    with pytest.raises(ValueError):
        assert_tenant_storage_key('other-tenant/file.pdf', 'tenant-1')


def test_storage_token_roundtrip():
    token = create_storage_token('tenant-1/documents/x.pdf', 'put', 60)
    assert verify_storage_token(token, 'tenant-1/documents/x.pdf', 'put')
    assert not verify_storage_token(token, 'tenant-1/documents/y.pdf', 'put')


@pytest.mark.asyncio
async def test_local_upload_read_delete(tmp_path, monkeypatch):
    monkeypatch.setenv('STORAGE_PROVIDER', 'local')
    monkeypatch.setenv('STORAGE_LOCAL_PATH', str(tmp_path))
    monkeypatch.setenv('JWT_SECRET', 'test-secret-key-at-least-32-chars-long!!')

    from src.core.config import get_settings

    get_settings.cache_clear() if hasattr(get_settings, 'cache_clear') else None
    from importlib import reload
    import src.core.config as config_mod

    reload(config_mod)
    import src.core.storage.client as client_mod

    reload(client_mod)
    svc = client_mod.StorageService()

    key = 'tenant-a/documents/2026/05/22/test.txt'
    up = await svc.upload_file(b'hello', key, content_type='text/plain')
    assert up['success'] is True

    meta = await svc.get_file_metadata(key)
    assert meta['success'] is True
    assert meta['content_length'] == 5

    read = await svc.read_file(key)
    assert read['content'] == b'hello'

    dl = await svc.generate_signed_download_url(key)
    assert dl['success'] is True
    assert '/api/v1/files/blob/' in dl['download_url']

    deleted = await svc.delete_file(key)
    assert deleted['success'] is True


def test_files_router_awaits_signed_urls():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'routers' / 'files.py').read_text(
        encoding='utf-8'
    )
    assert 'public_storage_router' in text
    assert 'await storage_service.generate_signed_upload_url' in text
    assert 'await storage_service.generate_signed_download_url' in text
    assert 'assert_tenant_storage_key' in text


def test_documents_router_awaits_signed_urls():
    text = (REPO / 'apps' / 'api' / 'src' / 'api' / 'routers' / 'documents.py').read_text(
        encoding='utf-8'
    )
    assert 'await storage_service.generate_signed_upload_url' in text
    assert 'await storage_service.generate_signed_download_url' in text


def test_ocr_worker_awaits_or_reads_local():
    text = (REPO / 'apps' / 'api' / 'src' / 'core' / 'ocr' / 'worker.py').read_text(encoding='utf-8')
    assert 'await storage_service.generate_signed_download_url' in text
    assert 'read_file' in text


def test_env_example_documents_storage_provider():
    text = (REPO / '.env.example').read_text(encoding='utf-8')
    assert 'STORAGE_PROVIDER=local' in text
    assert 'STORAGE_LOCAL_PATH=' in text
