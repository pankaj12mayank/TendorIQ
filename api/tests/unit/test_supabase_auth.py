"""Supabase JWT verification."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from jose import jwt

from src.core.supabase_auth import claims_email, verify_supabase_access_token


@pytest.fixture
def supabase_settings(monkeypatch):
    secret = 'test-supabase-jwt-secret-at-least-32-chars'
    mock = MagicMock()
    mock.AUTH_PROVIDER = 'supabase'
    mock.SUPABASE_URL = 'https://testproject.supabase.co'
    mock.SUPABASE_JWT_SECRET = secret
    monkeypatch.setattr('src.core.supabase_auth.settings', mock)
    return secret


def test_verify_supabase_access_token_valid(supabase_settings):
    sub = str(uuid4())
    email = 'user@example.com'
    token = jwt.encode(
        {
            'sub': sub,
            'email': email,
            'aud': 'authenticated',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        },
        supabase_settings,
        algorithm='HS256',
    )
    claims = verify_supabase_access_token(token)
    assert claims is not None
    assert claims['sub'] == sub
    assert claims_email(claims) == email


def test_verify_supabase_access_token_invalid(supabase_settings):
    assert verify_supabase_access_token('not-a-jwt') is None
