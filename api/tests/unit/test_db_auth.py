"""Database-only auth (no .env credential bypass)."""

from unittest.mock import MagicMock

from src.core.local_user_auth import PLATFORM_ADMIN_PREF, _password_hash
from src.core.passwords import hash_password, verify_password


def test_hash_and_verify_password():
    hashed = hash_password('secure-pass-123')
    assert verify_password('secure-pass-123', hashed)
    assert not verify_password('wrong', hashed)


def test_password_hash_from_preferences():
    user = MagicMock()
    user.preferences = {'password_hash': hash_password('x')}
    assert _password_hash(user) is not None


def test_platform_admin_pref_constant():
    assert PLATFORM_ADMIN_PREF == 'platform_super_admin'
