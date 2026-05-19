"""Encrypt/decrypt sensitive email provider credentials."""

import base64
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from ..config import settings

logger = logging.getLogger(__name__)


@lru_cache
def _fernet() -> Fernet:
    key_material = settings.ENCRYPTION_KEY or settings.JWT_SECRET
    digest = hashlib.sha256(key_material.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    if not value:
        return ''
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    if not value:
        return ''
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        logger.error('Failed to decrypt credential — invalid token or key rotation needed')
        raise ValueError('Unable to decrypt stored credential')
