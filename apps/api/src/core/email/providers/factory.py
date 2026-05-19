"""Build email providers from DB config with primary/fallback chain."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt_secret
from ..db_models import SmtpConfig
from ...config import settings
from .base import EmailProvider
from .mock_provider import MockProvider
from .resend_provider import ResendProvider
from .smtp_provider import SmtpProvider

logger = logging.getLogger(__name__)


async def get_provider_chain(db: AsyncSession, tenant_id: Optional[str] = None) -> list[EmailProvider]:
    """Return ordered providers: primary → fallback → env default → mock."""
    providers: list[EmailProvider] = []

    query = select(SmtpConfig).where(SmtpConfig.is_active == True).order_by(  # noqa: E712
        SmtpConfig.is_primary.desc(),
        SmtpConfig.is_fallback.asc(),
    )
    if tenant_id:
        query = query.where((SmtpConfig.tenant_id == tenant_id) | (SmtpConfig.tenant_id.is_(None)))
    else:
        query = query.where(SmtpConfig.tenant_id.is_(None))

    result = await db.execute(query)
    configs = result.scalars().all()

    for cfg in configs:
        if cfg.provider == 'resend':
            password = decrypt_secret(cfg.password_encrypted) if cfg.password_encrypted else settings.EMAIL_API_KEY
            providers.append(ResendProvider(api_key=password, from_email=cfg.from_email, from_name=cfg.from_name))
        elif cfg.provider == 'smtp' and cfg.host:
            providers.append(
                SmtpProvider(
                    host=cfg.host,
                    port=cfg.port or 587,
                    username=cfg.username or '',
                    password=decrypt_secret(cfg.password_encrypted) if cfg.password_encrypted else '',
                    from_email=cfg.from_email,
                    from_name=cfg.from_name,
                    encryption=cfg.encryption or 'tls',
                )
            )

    if not providers and settings.EMAIL_API_KEY:
        providers.append(ResendProvider(api_key=settings.EMAIL_API_KEY, from_email=settings.EMAIL_FROM, from_name=settings.EMAIL_FROM_NAME))

    if not providers:
        providers.append(MockProvider())

    return providers


async def send_with_fallback(providers: list[EmailProvider], email) -> tuple:
    """Try each provider until one succeeds."""
    from .base import SendResult

    last_error = 'No providers configured'
    for provider in providers:
        result = await provider.send(email)
        if result.success:
            return result, provider.name
        last_error = result.error or 'Unknown error'
        logger.warning('Provider %s failed: %s', provider.name, last_error)

    return SendResult(success=False, error=last_error), 'none'
