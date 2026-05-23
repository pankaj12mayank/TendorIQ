"""SSO configuration and session exchange API."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import AuthContext
from ...core.config import settings
from ...core.database import get_db
from ...core.sso import SSOConfig, SSOHandler, SSOProvider, SSOService
from ...core.sso.bootstrap import exchange_sso_session
from ...core.sso.tenant_store import (
    config_to_public,
    get_tenant_by_slug,
    load_sso_config,
    save_sso_config,
)
from ..dependencies.auth import get_current_user
from ..dependencies.rbac_deps import RequireOrgUpdate, RequireSettingsRead, TenantMember
from ..routers.auth import LoginResponse, _login_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/sso', tags=['SSO'])


def _sso_feature_enabled() -> bool:
    return bool(getattr(settings, 'FEATURE_SSO', False))


def _require_sso_feature() -> None:
    if not _sso_feature_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Enterprise SSO is disabled (FEATURE_SSO=false)',
        )


class SSOConfigRequest(BaseModel):
    provider: SSOProvider
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    domain: Optional[str] = None
    metadata_url: Optional[str] = None
    idp_entity_id: Optional[str] = None
    enabled: bool = True


class SSOConfigResponse(BaseModel):
    provider: str
    enabled: bool
    domain: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None


class SSOSessionRequest(BaseModel):
    org_slug: str = Field(..., min_length=2)
    token: str = Field(..., min_length=3)


class SSOAuthRequest(BaseModel):
    token: str


@router.get('/providers')
async def list_providers(
    current_user: AuthContext = Depends(get_current_user),
):
    _require_sso_feature()
    return await SSOService.list_providers()


@router.post('/configure')
async def configure_sso(
    config: SSOConfigRequest,
    current_user: RequireOrgUpdate,
    db: AsyncSession = Depends(get_db),
):
    _require_sso_feature()
    sso_config = SSOConfig(
        provider=config.provider,
        enabled=config.enabled,
        client_id=config.client_id,
        client_secret=config.client_secret,
        tenant_id=config.tenant_id,
        domain=config.domain,
        metadata_url=config.metadata_url,
        idp_entity_id=config.idp_entity_id,
    )
    return await save_sso_config(db, UUID(current_user.tenant_id), sso_config)


@router.get('/config', response_model=SSOConfigResponse)
async def get_sso_config(
    current_user: RequireSettingsRead,
    db: AsyncSession = Depends(get_db),
):
    _require_sso_feature()
    config = await load_sso_config(db, UUID(current_user.tenant_id))
    if not config:
        return SSOConfigResponse(provider='none', enabled=False)
    public = config_to_public(config)
    return SSOConfigResponse(
        provider=public['provider'],
        enabled=public['enabled'],
        domain=public.get('domain'),
        tenant_id=public.get('tenant_id'),
        client_id=public.get('client_id'),
    )


@router.post('/disable')
async def disable_sso(
    current_user: RequireOrgUpdate,
    db: AsyncSession = Depends(get_db),
):
    _require_sso_feature()
    existing = await load_sso_config(db, UUID(current_user.tenant_id))
    provider = existing.provider if existing else SSOProvider.OKTA
    return await save_sso_config(
        db,
        UUID(current_user.tenant_id),
        SSOConfig(provider=provider, enabled=False),
    )


@router.get('/login-url')
async def get_sso_login_url(
    current_user: TenantMember,
    redirect_uri: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    _require_sso_feature()
    config = await load_sso_config(db, UUID(current_user.tenant_id))
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail='SSO not configured for this organization')
    handler = SSOHandler(config)
    return {'url': handler.get_login_url(redirect_uri)}


@router.post('/authenticate')
async def authenticate_sso(
    request: SSOAuthRequest,
    current_user: TenantMember,
    db: AsyncSession = Depends(get_db),
):
    """Validate SSO token for an already authenticated tenant admin session."""
    _require_sso_feature()
    config = await load_sso_config(db, UUID(current_user.tenant_id))
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail='SSO not enabled')
    handler = SSOHandler(config)
    user = await handler.authenticate(request.token)
    mapping = handler.map_groups_to_roles(user.groups)
    return {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'groups': user.groups,
        'membership_role': mapping['membership_role'],
        'permissions': mapping['permissions'],
    }


@router.get('/public/config')
async def public_sso_config(
    org_slug: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
):
    """Public SSO availability for sign-in page (no secrets)."""
    _require_sso_feature()
    tenant = await get_tenant_by_slug(db, org_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail='Organization not found')
    config = await load_sso_config(db, tenant.id)
    if not config or not config.enabled:
        return {'enabled': False, 'provider': 'none', 'org_slug': org_slug}
    public = config_to_public(config)
    return {
        'enabled': True,
        'provider': public['provider'],
        'org_slug': org_slug,
        'domain': public.get('domain'),
    }


@router.get('/public/login-url')
async def public_sso_login_url(
    org_slug: str = Query(..., min_length=2),
    redirect_uri: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    _require_sso_feature()
    tenant = await get_tenant_by_slug(db, org_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail='Organization not found')
    config = await load_sso_config(db, tenant.id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail='SSO not enabled for organization')
    handler = SSOHandler(config)
    return {'url': handler.get_login_url(redirect_uri)}


@router.post('/session', response_model=LoginResponse)
async def sso_session_exchange(
    body: SSOSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Exchange an IdP token for a TenderIQ JWT (public, org-scoped)."""
    _require_sso_feature()
    tenant = await get_tenant_by_slug(db, body.org_slug.strip().lower())
    if not tenant:
        raise HTTPException(status_code=404, detail='Organization not found')
    config = await load_sso_config(db, tenant.id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail='SSO not enabled for organization')

    handler = SSOHandler(config)
    try:
        sso_user = await handler.authenticate(body.token)
        mapping = handler.map_groups_to_roles(sso_user.groups)
        exchanged = await exchange_sso_session(
            db,
            tenant_id=tenant.id,
            sso_user=sso_user,
            membership_role=mapping['membership_role'],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception('SSO session exchange failed')
        raise HTTPException(status_code=401, detail='SSO authentication failed') from exc

    return _login_response(
        'SSO session exchanged',
        exchanged['user'],
        exchanged['tokens'],
    )


__all__ = ['router']
