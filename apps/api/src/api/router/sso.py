"""SSO Configuration API"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.sso import SSOProvider, SSOConfig, SSOService, SSOUser
from ..dependencies.auth import get_current_user
from ...core.auth import AuthContext

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/sso', tags=['SSO'])


class SSOConfigRequest(BaseModel):
    provider: SSOProvider
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    domain: Optional[str] = None
    metadata_url: Optional[str] = None
    idp_entity_id: Optional[str] = None


class SSOConfigResponse(BaseModel):
    provider: str
    enabled: bool
    domain: Optional[str] = None
    tenant_id: Optional[str] = None


class SSOAuthRequest(BaseModel):
    token: str


@router.get('/providers')
async def list_providers(
    current_user: AuthContext = Depends(get_current_user),
):
    """List available SSO providers"""
    return await SSOService.list_providers()


@router.post('/configure')
async def configure_sso(
    config: SSOConfigRequest,
    current_user: AuthContext = Depends(get_current_user),
):
    """Configure SSO for organization"""
    if current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=403,
            detail="Only admins can configure SSO"
        )
    
    sso_config = SSOConfig(
        provider=config.provider,
        enabled=True,
        client_id=config.client_id,
        client_secret=config.client_secret,
        tenant_id=config.tenant_id,
        domain=config.domain,
        metadata_url=config.metadata_url,
        idp_entity_id=config.idp_entity_id,
    )
    
    tenant_id = str(current_user.tenant_id)
    result = await SSOService.configure(tenant_id, sso_config)
    
    return result


@router.get('/config', response_model=SSOConfigResponse)
async def get_sso_config(
    current_user: AuthContext = Depends(get_current_user),
):
    """Get current SSO configuration"""
    tenant_id = str(current_user.tenant_id)
    config = await SSOService.get_config(tenant_id)
    
    if not config:
        return SSOConfigResponse(
            provider="none",
            enabled=False,
        )
    
    return SSOConfigResponse(
        provider=config.provider.value,
        enabled=config.enabled,
        domain=config.domain,
        tenant_id=config.tenant_id,
    )


@router.post('/authenticate')
async def authenticate_sso(
    request: SSOAuthRequest,
    current_user: AuthContext = Depends(get_current_user),
):
    """Authenticate via SSO token"""
    tenant_id = str(current_user.tenant_id)
    
    try:
        user = await SSOService.authenticate(tenant_id, request.token)
        
        # Map SSO groups to roles
        from ...core.sso import SSOHandler
        handler = SSOHandler(SSOConfig(provider=SSOProvider.OKTA, enabled=True))
        role_mapping = handler.map_groups_to_roles(user.groups)
        
        return {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "groups": user.groups,
            "roles": role_mapping['roles'],
            "permissions": role_mapping['permissions'],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO authentication failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="SSO authentication failed"
        )


@router.get('/login-url')
async def get_sso_login_url(
    redirect_uri: str = Query(...),
    current_user: AuthContext = Depends(get_current_user),
):
    """Get SSO login URL"""
    tenant_id = str(current_user.tenant_id)
    
    try:
        login_url = await SSOService.get_login_url(tenant_id, redirect_uri)
        return {"url": login_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SSO login URL: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate SSO login URL"
        )


@router.post('/disable')
async def disable_sso(
    current_user: AuthContext = Depends(get_current_user),
):
    """Disable SSO for organization"""
    if current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=403,
            detail="Only admins can disable SSO"
        )
    
    tenant_id = str(current_user.tenant_id)
    await SSOService.configure(
        tenant_id,
        SSOConfig(provider=SSOProvider.OKTA, enabled=False)
    )
    
    return {"success": True, "message": "SSO disabled"}


__all__ = ['router']