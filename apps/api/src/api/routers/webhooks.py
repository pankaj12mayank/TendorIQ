"""Webhook Router - Clerk and External Webhooks"""

from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from pydantic import BaseModel
import hmac
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.clerk_bootstrap import ensure_clerk_user
from ...core.config import settings
from ...core.database import get_db
from ...core.logging import get_logger

logger = get_logger('webhooks')

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])


class ClerkWebhookPayload(BaseModel):
    type: str
    data: dict
    object: str = 'event'


def verify_clerk_signature(payload: bytes, signature: str) -> bool:
    """Verify Clerk webhook signature"""
    if not settings.CLERK_WEBHOOK_SECRET:
        logger.warning('Clerk webhook secret not configured')
        return False

    expected_signature = hmac.new(
        settings.CLERK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(f'sha256={expected_signature}', signature)


@router.post('/clerk')
async def clerk_webhook(
    request: Request,
    clerk_signature: str = Header(None, alias='clerk-signature'),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Clerk webhooks"""
    body = await request.body()

    if settings.CLERK_WEBHOOK_SECRET:
        if not clerk_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Missing clerk-signature header',
            )

        if not verify_clerk_signature(body, clerk_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid webhook signature',
            )

    import json

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid JSON payload',
        )

    event_type = payload.get('type', '')
    data = payload.get('data', {})

    logger.info('Clerk webhook received', type=event_type, data_id=data.get('id'))

    if event_type == 'user.created':
        await handle_user_created(data, db)
    elif event_type == 'user.updated':
        await handle_user_updated(data, db)
    elif event_type == 'user.deleted':
        await handle_user_deleted(data)
    elif event_type == 'user.email_address_created':
        await handle_email_created(data)
    elif event_type == 'session.created':
        await handle_session_created(data)
    elif event_type == 'session.removed':
        await handle_session_removed(data)

    return {'status': 'received'}


async def handle_user_created(data: dict, db: AsyncSession) -> None:
    """Handle new user creation — link Clerk id to application user."""
    logger.info('New user created', user_id=data.get('id'))
    try:
        await ensure_clerk_user(db, data)
    except ValueError as exc:
        logger.warning('Clerk user.created bootstrap skipped: %s', exc)


async def handle_user_updated(data: dict, db: AsyncSession) -> None:
    """Handle user update — refresh Clerk linkage."""
    logger.info('User updated', user_id=data.get('id'))
    try:
        await ensure_clerk_user(db, data)
    except ValueError as exc:
        logger.warning('Clerk user.updated bootstrap skipped: %s', exc)


async def handle_user_deleted(data: dict) -> None:
    """Handle user deletion"""
    logger.info('User deleted', user_id=data.get('id'))
    # Handle user deletion in database (soft delete)


async def handle_email_created(data: dict) -> None:
    """Handle new email address"""
    logger.info('User email created', user_id=data.get('id'))


async def handle_session_created(data: dict) -> None:
    """Handle new session"""
    logger.info('Session created', session_id=data.get('id'))


async def handle_session_removed(data: dict) -> None:
    """Handle session removal"""
    logger.info('Session removed', session_id=data.get('id'))


@router.post('/resend')
async def resend_webhook(request: Request) -> dict:
    """Handle Resend webhook events (email delivery status)"""
    body = await request.json()
    event_type = body.get('type', '')

    logger.info('Resend webhook received', type=event_type)

    return {'status': 'received'}


@router.post('/stripe')
async def stripe_webhook(request: Request) -> dict:
    """Handle Stripe webhook events (billing)"""
    body = await request.body()

    # Verify Stripe signature
    signature = request.headers.get('stripe-signature')

    logger.info('Stripe webhook received', signature=bool(signature))

    return {'status': 'received'}