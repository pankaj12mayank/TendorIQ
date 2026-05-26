"""Verify Supabase access tokens (JWT)."""

from __future__ import annotations

from typing import Any, Optional

from jose import JWTError, jwt

from .config import settings
from .logging import get_logger

logger = get_logger('supabase_auth')


def _supabase_ready() -> bool:
    secret = (settings.SUPABASE_JWT_SECRET or '').strip()
    url = (settings.SUPABASE_URL or '').strip()
    return (
        settings.AUTH_PROVIDER == 'supabase'
        and bool(secret)
        and 'placeholder' not in secret.lower()
        and bool(url)
        and 'placeholder' not in url.lower()
    )


def verify_supabase_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a Supabase Auth JWT. Returns claims or None."""
    if not _supabase_ready():
        return None
    secret = settings.SUPABASE_JWT_SECRET.strip()
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=['HS256'],
            audience='authenticated',
            options={'verify_aud': True},
        )
        if not payload.get('sub'):
            return None
        return payload
    except JWTError as exc:
        logger.debug('Supabase JWT verification failed: %s', exc)
        return None


def claims_email(claims: dict[str, Any]) -> Optional[str]:
    email = claims.get('email')
    if email:
        return str(email).strip().lower()
    meta = claims.get('user_metadata') or {}
    if isinstance(meta, dict) and meta.get('email'):
        return str(meta['email']).strip().lower()
    return None


def claims_name(claims: dict[str, Any], email: Optional[str]) -> str:
    meta = claims.get('user_metadata') or {}
    if isinstance(meta, dict):
        full = (meta.get('full_name') or meta.get('name') or '').strip()
        if full:
            return full
    if email and '@' in email:
        return email.split('@')[0]
    return 'User'
