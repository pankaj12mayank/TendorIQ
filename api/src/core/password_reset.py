"""Password reset token lifecycle and delivery."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .local_user_auth import _password_hash, _set_user_prefs, _user_prefs
from .mailer import send_smtp_email
from .models import PasswordResetToken, User, generate_uuid, pk_str
from .passwords import hash_password
from .smtp_settings import get_smtp_settings

TOKEN_TTL_MINUTES = 30
MAX_ACTIVE_TOKENS_PER_USER = 5


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _new_token() -> str:
    return secrets.token_urlsafe(32)


async def _cleanup_expired(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        delete(PasswordResetToken).where(
            (PasswordResetToken.expires_at < now) | (PasswordResetToken.used_at.is_not(None))
        )
    )


async def request_password_reset(
    db: AsyncSession,
    *,
    email: str,
    request_ip: Optional[str],
) -> None:
    """Generate token and send reset email if account exists. Silent for unknown emails."""
    normalized = email.strip().lower()
    if not normalized:
        return

    user = (await db.execute(select(User).where(User.email == normalized))).scalar_one_or_none()
    if not user or not _password_hash(user):
        return

    await _cleanup_expired(db)
    active = (
        await db.execute(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == pk_str(user.id),
                PasswordResetToken.used_at.is_(None),
            )
            .order_by(PasswordResetToken.created_at.asc())
        )
    ).scalars().all()
    overflow = max(0, len(active) - (MAX_ACTIVE_TOKENS_PER_USER - 1))
    for stale in active[:overflow]:
        await db.delete(stale)

    raw_token = _new_token()
    token_row = PasswordResetToken(
        id=generate_uuid(),
        user_id=pk_str(user.id),
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES),
        requested_ip=request_ip,
    )
    db.add(token_row)
    await db.commit()

    smtp = await get_smtp_settings(db)
    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={raw_token}"
    body = (
        f'Hi {user.name or "there"},\n\n'
        'We received a password reset request for your TenderIQ account.\n'
        f'Use this link to reset your password (valid for {TOKEN_TTL_MINUTES} minutes):\n\n'
        f'{reset_link}\n\n'
        'If you did not request this, you can safely ignore this email.\n'
    )
    send_smtp_email(
        smtp_settings=smtp,
        to_email=user.email,
        subject='TenderIQ password reset',
        text_body=body,
    )


async def verify_reset_token(db: AsyncSession, token: str) -> tuple[bool, str]:
    hashed = _hash_token(token.strip())
    row = (
        await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed))
    ).scalar_one_or_none()
    if not row:
        return False, 'Invalid reset token'
    if row.used_at is not None:
        return False, 'Reset token already used'
    if row.expires_at < datetime.now(timezone.utc):
        return False, 'Reset token expired'
    return True, 'Token valid'


async def consume_reset_token_and_update_password(
    db: AsyncSession,
    *,
    token: str,
    new_password: str,
) -> None:
    if len(new_password) < 8:
        raise ValueError('New password must be at least 8 characters')

    hashed = _hash_token(token.strip())
    row = (
        await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed))
    ).scalar_one_or_none()
    if not row:
        raise ValueError('Invalid reset token')
    if row.used_at is not None:
        raise ValueError('Reset token already used')
    if row.expires_at < datetime.now(timezone.utc):
        raise ValueError('Reset token expired')

    user = await db.get(User, pk_str(row.user_id))
    if not user:
        raise ValueError('User not found')

    prefs = _user_prefs(user)
    prefs['password_hash'] = hash_password(new_password)
    _set_user_prefs(user, prefs)
    row.used_at = datetime.now(timezone.utc)
    await db.commit()
