"""External webhooks (Resend, Stripe). Clerk lives at POST /api/v1/auth/clerk/webhook."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_db
from ...core.billing.stripe_webhook import apply_stripe_webhook_event
from ...core.email.resend_webhook import apply_resend_webhook_event
from ...core.logging import get_logger
from ...core.svix_support import SVIX_AVAILABLE, Webhook, WebhookVerificationError

logger = get_logger('webhooks')

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])


def _verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    if not secret or not sig_header:
        return False
    parts: dict[str, str] = {}
    for item in sig_header.split(','):
        if '=' in item:
            key, value = item.split('=', 1)
            parts[key.strip()] = value.strip()
    timestamp = parts.get('t')
    signature = parts.get('v1')
    if not timestamp or not signature:
        return False
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except ValueError:
        return False
    signed = f'{timestamp}.{payload.decode("utf-8")}'.encode('utf-8')
    expected = hmac.new(secret.encode('utf-8'), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _verify_svix_delivery(body: bytes, request: Request, secret: str) -> None:
    if not secret:
        logger.warning('Webhook secret not set — skipping signature verification')
        return
    if not SVIX_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Webhooks require the svix package (pip install -r requirements-dev.txt)',
        )
    wh = Webhook(secret)
    try:
        wh.verify(
            body,
            {
                'svix-id': request.headers.get('svix-id') or '',
                'svix-timestamp': request.headers.get('svix-timestamp') or '',
                'svix-signature': request.headers.get('svix-signature') or '',
            },
        )
    except WebhookVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid webhook signature',
        ) from exc


@router.post('/resend')
async def resend_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Handle Resend delivery events (Svix-signed) and sync email_logs."""
    body = await request.body()
    _verify_svix_delivery(body, request, (settings.RESEND_WEBHOOK_SECRET or '').strip())
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid JSON') from exc

    result = await apply_resend_webhook_event(db, payload)
    logger.info('Resend webhook processed', type=payload.get('type', ''), handled=result.get('handled'))
    return {'status': 'received', **result}


@router.post('/stripe')
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Handle Stripe billing webhooks and sync tenant subscription state."""
    body = await request.body()
    signature = request.headers.get('stripe-signature', '')
    secret = (settings.STRIPE_WEBHOOK_SECRET or '').strip()

    if secret:
        if not _verify_stripe_signature(body, signature, secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid Stripe webhook signature',
            )
    else:
        logger.warning('STRIPE_WEBHOOK_SECRET not set — skipping signature verification')

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid JSON') from exc

    result = await apply_stripe_webhook_event(db, payload)
    logger.info('Stripe webhook processed', type=payload.get('type', ''), handled=result.get('handled'))
    return {'status': 'received', **result}
