"""SMTP settings storage (admin-managed, encrypted at rest)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .platform.lite_settings import get_setting, patch_setting
from .security.encrypted_secrets import SecretEncryptor

SMTP_SECTION = 'smtp'
SECRET_KEYS = ('app_password',)

DEFAULT_SMTP: dict[str, Any] = {
    'host': '',
    'port': 587,
    'sender_email': '',
    'sender_name': 'TenderIQ',
    'app_password': '',
}


def _encrypt_secret(value: str) -> str:
    if not value:
        return ''
    if value.startswith('ENC:'):
        return value
    enc = SecretEncryptor().encrypt(value)
    return f'ENC:{enc}'


def _decrypt_secret(value: str) -> str:
    if not value:
        return ''
    if not value.startswith('ENC:'):
        return value
    return SecretEncryptor().decrypt(value[4:])


def _sanitize_out(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(DEFAULT_SMTP)
    out.update({k: v for k, v in data.items() if v is not None})
    out['port'] = int(out.get('port') or 587)
    out['app_password'] = _decrypt_secret(str(out.get('app_password') or ''))
    return out


def _sanitize_store(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(DEFAULT_SMTP)
    out.update({k: v for k, v in data.items() if v is not None})
    out['host'] = str(out.get('host') or '').strip()
    out['sender_email'] = str(out.get('sender_email') or '').strip().lower()
    out['sender_name'] = str(out.get('sender_name') or 'TenderIQ').strip() or 'TenderIQ'
    out['port'] = int(out.get('port') or 587)
    for key in SECRET_KEYS:
        out[key] = _encrypt_secret(str(out.get(key) or ''))
    return out


async def get_smtp_settings(db: AsyncSession) -> dict[str, Any]:
    raw = await get_setting(db, SMTP_SECTION)
    return _sanitize_out(raw)


async def update_smtp_settings(db: AsyncSession, patch: dict[str, Any]) -> dict[str, Any]:
    current = await get_setting(db, SMTP_SECTION)
    merged = dict(current)
    merged.update(patch)
    stored = _sanitize_store(merged)
    await patch_setting(db, SMTP_SECTION, stored)
    return _sanitize_out(stored)


def is_smtp_configured(settings_row: dict[str, Any]) -> bool:
    return bool(
        str(settings_row.get('host') or '').strip()
        and str(settings_row.get('sender_email') or '').strip()
        and str(settings_row.get('app_password') or '').strip()
    )
