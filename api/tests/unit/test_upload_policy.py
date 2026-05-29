"""Lite upload policy and storage validation."""

import pytest

from src.core.storage.client import StorageService
from src.core.upload_policy import LITE_ALLOWED_EXTENSIONS, LITE_MAX_FILE_SIZE_MB


@pytest.fixture
def storage(monkeypatch):
    monkeypatch.setenv('STORAGE_MAX_FILE_SIZE_MB', str(LITE_MAX_FILE_SIZE_MB))
    monkeypatch.setenv('STORAGE_ALLOWED_EXTENSIONS', ','.join(LITE_ALLOWED_EXTENSIONS))
    return StorageService()


def test_lite_rejects_png(storage):
    ok, msg = storage.validate_file('scan.png', 1024)
    assert ok is False
    assert 'not allowed' in (msg or '').lower()


def test_lite_accepts_pdf_within_limit(storage):
    ok, msg = storage.validate_file('tender.pdf', 1024)
    assert ok is True
    assert msg is None


def test_lite_accepts_doc_within_limit(storage):
    ok, msg = storage.validate_file('spec.doc', 1024)
    assert ok is True
    assert msg is None


def test_lite_rejects_oversize(storage):
    max_bytes = LITE_MAX_FILE_SIZE_MB * 1024 * 1024
    ok, msg = storage.validate_file('big.pdf', max_bytes + 1)
    assert ok is False
    assert '25' in (msg or '')


def test_storage_key_user_prefix(storage):
    key = storage.generate_storage_key(
        tenant_id='tenant-1',
        filename='doc.pdf',
        owner_id='user-abc',
    )
    assert key.startswith('users/user-abc/documents/')
