"""Resolve payment gateway credentials (platform settings + env fallbacks)."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..platform.lite_settings import get_setting

try:
    import razorpay

    RAZORPAY_SDK = True
except ImportError:
    razorpay = None  # type: ignore
    RAZORPAY_SDK = False


def _decode_secret(value: str) -> str:
    v = (value or '').strip()
    if not v or not v.startswith('ENC:'):
        return v
    from ..security.encrypted_secrets import SecretEncryptor

    return SecretEncryptor().decrypt(v[4:])


def _decode_gateway_secrets(cfg: dict[str, Any]) -> dict[str, Any]:
    out = dict(cfg or {})
    for key in ('razorpay_key_secret', 'stripe_secret_key', 'stripe_webhook_secret'):
        if key in out:
            out[key] = _decode_secret(str(out.get(key) or ''))
    return out


async def load_gateway_config(db: AsyncSession) -> dict[str, Any]:
    raw = await get_setting(db, 'payment_gateways')
    cfg = _decode_gateway_secrets(raw if isinstance(raw, dict) else {})
    key_id = (str(cfg.get('razorpay_key_id') or '').strip() or (settings.RAZORPAY_KEY_ID or '').strip())
    key_secret = (
        str(cfg.get('razorpay_key_secret') or '').strip() or (settings.RAZORPAY_KEY_SECRET or '').strip()
    )
    stripe_secret = str(cfg.get('stripe_secret_key') or '').strip()
    stripe_publishable = str(cfg.get('stripe_publishable_key') or '').strip()
    return {
        **cfg,
        'razorpay_key_id': key_id,
        'razorpay_key_secret': key_secret,
        'stripe_secret_key': stripe_secret,
        'stripe_publishable_key': stripe_publishable,
    }


def razorpay_enabled(cfg: dict[str, Any]) -> bool:
    key = str(cfg.get('razorpay_key_id') or '').strip()
    secret = str(cfg.get('razorpay_key_secret') or '').strip()
    if not key or not secret or not RAZORPAY_SDK:
        return False
    if 'placeholder' in key.lower() or 'placeholder' in secret.lower():
        return False
    return True


def stripe_enabled(cfg: dict[str, Any]) -> bool:
    return bool(str(cfg.get('stripe_secret_key') or '').strip())


def payment_enabled(cfg: dict[str, Any]) -> bool:
    return razorpay_enabled(cfg) or stripe_enabled(cfg)


def preferred_provider(cfg: dict[str, Any]) -> Optional[str]:
    if stripe_enabled(cfg):
        return 'stripe'
    if razorpay_enabled(cfg):
        return 'razorpay'
    return None


def razorpay_client(cfg: dict[str, Any]):
    if not razorpay_enabled(cfg):
        raise ValueError('Online payment is not available')
    return razorpay.Client(auth=(cfg['razorpay_key_id'], cfg['razorpay_key_secret']))
