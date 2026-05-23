"""Layer 34 — Storage paths & signed URL clock skew."""

import time
from pathlib import Path

import pytest

from src.core.local_storage_paths import api_app_root, resolve_storage_local_path
from src.core.storage.tokens import create_storage_token, verify_storage_token

REPO = Path(__file__).resolve().parents[4]


def test_paths_module_exists():
    text = (REPO / 'apps' / 'api' / 'src' / 'core' / 'local_storage_paths.py').read_text(
        encoding='utf-8'
    )
    assert 'resolve_storage_local_path' in text
    assert 'api_app_root' in text
    storage_paths = (REPO / 'apps' / 'api' / 'src' / 'core' / 'storage' / 'paths.py').read_text(
        encoding='utf-8'
    )
    assert 'ensure_local_storage_root' in storage_paths


def test_relative_uploads_resolves_under_api_app():
    base = api_app_root()
    resolved = resolve_storage_local_path('./uploads', base=base)
    assert resolved.is_absolute()
    assert resolved == (base / 'uploads').resolve()
    assert resolved.name == 'uploads'


def test_config_normalizes_storage_local_path(monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_LOCAL_PATH', './uploads')
    monkeypatch.setenv('JWT_SECRET', 'test-secret-key-at-least-32-chars-long!!')
    monkeypatch.setenv('DATABASE_URL', 'mysql+aiomysql://u:p@localhost/t')

    from importlib import reload
    import src.core.config as config_mod

    if hasattr(config_mod.get_settings, 'cache_clear'):
        config_mod.get_settings.cache_clear()
    reload(config_mod)
    s = config_mod.get_settings()
    assert Path(s.STORAGE_LOCAL_PATH).is_absolute()
    assert s.resolved_storage_local_path == Path(s.STORAGE_LOCAL_PATH)


def test_token_clock_skew_accepts_recently_expired(monkeypatch):
    monkeypatch.setenv('STORAGE_TOKEN_CLOCK_SKEW_SECONDS', '300')
    monkeypatch.setenv('JWT_SECRET', 'test-secret-key-at-least-32-chars-long!!')

    from importlib import reload
    import src.core.config as config_mod

    if hasattr(config_mod.get_settings, 'cache_clear'):
        config_mod.get_settings.cache_clear()
    reload(config_mod)
    import src.core.storage.tokens as tokens_mod

    reload(tokens_mod)

    key = 'tenant-1/documents/f.pdf'
    expires_at = int(time.time()) - 30
    payload = f'put:{key}:{expires_at}'
    import hashlib
    import hmac

    from src.core.config import settings

    sig = hmac.new(
        settings.JWT_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    token = f'{expires_at}.{sig}'
    assert tokens_mod.verify_storage_token(token, key, 'put')


def test_main_ensures_local_storage_on_startup():
    text = (REPO / 'apps' / 'api' / 'src' / 'main.py').read_text(encoding='utf-8')
    assert 'ensure_local_storage_root' in text


def test_env_example_documents_clock_skew():
    text = (REPO / '.env.example').read_text(encoding='utf-8')
    assert 'STORAGE_TOKEN_CLOCK_SKEW_SECONDS' in text


def test_storage_doc_mentions_path_and_skew():
    text = (REPO / 'docs' / 'storage.md').read_text(encoding='utf-8')
    assert 'apps/api' in text
    assert 'STORAGE_TOKEN_CLOCK_SKEW_SECONDS' in text


def test_client_uses_resolved_storage_path():
    text = (REPO / 'apps' / 'api' / 'src' / 'core' / 'storage' / 'client.py').read_text(
        encoding='utf-8'
    )
    assert 'resolved_storage_local_path' in text
