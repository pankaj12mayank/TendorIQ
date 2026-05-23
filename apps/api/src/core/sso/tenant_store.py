"""Persist enterprise SSO configuration on ``tenants.settings``."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Tenant
from . import SSOConfig, SSOProvider

SSO_SETTINGS_KEY = 'sso'


def _config_from_dict(raw: dict[str, Any]) -> SSOConfig:
    provider = raw.get('provider') or SSOProvider.OKTA.value
    try:
        provider_enum = SSOProvider(provider)
    except ValueError:
        provider_enum = SSOProvider.OKTA
    return SSOConfig(
        provider=provider_enum,
        enabled=bool(raw.get('enabled')),
        client_id=raw.get('client_id'),
        client_secret=raw.get('client_secret'),
        tenant_id=raw.get('tenant_id'),
        domain=raw.get('domain'),
        metadata_url=raw.get('metadata_url'),
        idp_entity_id=raw.get('idp_entity_id'),
        sp_entity_id=raw.get('sp_entity_id') or 'tenderiq',
        acs_url=raw.get('acs_url'),
    )


def config_to_dict(config: SSOConfig) -> dict[str, Any]:
    return {
        'provider': config.provider.value,
        'enabled': config.enabled,
        'client_id': config.client_id,
        'client_secret': config.client_secret,
        'tenant_id': config.tenant_id,
        'domain': config.domain,
        'metadata_url': config.metadata_url,
        'idp_entity_id': config.idp_entity_id,
        'sp_entity_id': config.sp_entity_id,
        'acs_url': config.acs_url,
    }


def config_to_public(config: SSOConfig) -> dict[str, Any]:
    data = config_to_dict(config)
    data.pop('client_secret', None)
    return data


async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Optional[Tenant]:
    result = await db.execute(select(Tenant).where(Tenant.slug == slug.strip().lower()))
    return result.scalar_one_or_none()


async def load_sso_config(db: AsyncSession, tenant_id: UUID | str) -> Optional[SSOConfig]:
    tid = tenant_id if isinstance(tenant_id, UUID) else UUID(str(tenant_id))
    tenant = await db.get(Tenant, tid)
    if not tenant:
        return None
    settings = tenant.settings or {}
    raw = settings.get(SSO_SETTINGS_KEY)
    if not raw or not isinstance(raw, dict):
        return None
    return _config_from_dict(raw)


async def save_sso_config(db: AsyncSession, tenant_id: UUID | str, config: SSOConfig) -> dict[str, Any]:
    tid = tenant_id if isinstance(tenant_id, UUID) else UUID(str(tenant_id))
    tenant = await db.get(Tenant, tid)
    if not tenant:
        raise ValueError('Tenant not found')
    settings = dict(tenant.settings or {})
    settings[SSO_SETTINGS_KEY] = config_to_dict(config)
    tenant.settings = settings
    await db.commit()
    await db.refresh(tenant)
    return {'success': True, 'provider': config.provider.value, 'enabled': config.enabled}
