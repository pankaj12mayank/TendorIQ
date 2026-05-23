"""Short-lived HMAC tokens for local storage PUT/GET without S3 presign."""

import hashlib
import hmac
import time
from typing import Optional

from ..config import settings


def _secret() -> bytes:
    return settings.JWT_SECRET.encode('utf-8')


def create_storage_token(storage_key: str, action: str, expires_seconds: int = 3600) -> str:
    expires_at = int(time.time()) + expires_seconds
    payload = f'{action}:{storage_key}:{expires_at}'
    sig = hmac.new(_secret(), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f'{expires_at}.{sig}'


def verify_storage_token(token: str, storage_key: str, action: str) -> bool:
    try:
        expires_str, sig = token.split('.', 1)
        expires_at = int(expires_str)
    except ValueError:
        return False
    skew = settings.STORAGE_TOKEN_CLOCK_SKEW_SECONDS
    if expires_at + skew < int(time.time()):
        return False
    payload = f'{action}:{storage_key}:{expires_at}'
    expected = hmac.new(_secret(), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
