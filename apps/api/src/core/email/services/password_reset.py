"""Secure password reset token generation and validation."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import PasswordResetToken
from ...config import settings
from .dispatcher import EmailDispatcher


class PasswordResetService:
    TOKEN_EXPIRY_HOURS = 1

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dispatcher = EmailDispatcher(db)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def request_reset(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """Create token and queue reset email. Always returns True (no email enumeration)."""
        raw_token = secrets.token_urlsafe(48)
        token_hash = self._hash_token(raw_token)
        expires = datetime.now(timezone.utc) + timedelta(hours=self.TOKEN_EXPIRY_HOURS)

        self.db.add(
            PasswordResetToken(
                email=email.lower().strip(),
                token_hash=token_hash,
                expires_at=expires,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        await self.db.flush()

        reset_link = f'{settings.FRONTEND_URL}/reset-password?token={raw_token}'
        await self.dispatcher.dispatch(
            'auth.forgot_password',
            email,
            {
                'user_name': email.split('@')[0],
                'reset_link': reset_link,
                'expires_in': '1 hour',
            },
            tenant_id=tenant_id,
            priority=10,
        )
        await self.db.commit()
        return True

    async def validate_token(self, raw_token: str) -> Optional[str]:
        """Return email if token valid, else None."""
        token_hash = self._hash_token(raw_token)
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        if row.expires_at < datetime.now(timezone.utc):
            return None
        return row.email

    async def consume_token(self, raw_token: str, new_password_hash: Optional[str] = None) -> bool:
        """Mark token used after password reset."""
        token_hash = self._hash_token(raw_token)
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
            )
        )
        row = result.scalar_one_or_none()
        if not row or row.expires_at < datetime.now(timezone.utc):
            return False

        row.used_at = datetime.now(timezone.utc)
        await self.db.flush()

        await self.dispatcher.dispatch(
            'auth.password.changed',
            row.email,
            {'user_name': row.email.split('@')[0]},
        )
        await self.db.commit()
        return True
