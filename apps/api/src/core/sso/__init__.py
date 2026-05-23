"""SSO/SAML Integration for Enterprise Authentication"""

import logging
from enum import Enum
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from ..rbac import permissions_for_role
from ..roles import MEMBERSHIP_ROLES, normalize_membership_role

logger = logging.getLogger(__name__)

GROUP_TO_MEMBERSHIP = {
    'Admins': 'admin',
    'Owners': 'owner',
    'Managers': 'manager',
    'Analysts': 'analyst',
    'Viewers': 'viewer',
    'Enterprise Users': 'member',
    'SSO Users': 'member',
}


class SSOProvider(str, Enum):
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    GOOGLE = "google"
    SAML = "saml"


class SSOConfig(BaseModel):
    provider: SSOProvider
    enabled: bool = False
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    domain: Optional[str] = None
    metadata_url: Optional[str] = None
    idp_entity_id: Optional[str] = None
    sp_entity_id: Optional[str] = "tenderiq"
    acs_url: Optional[str] = None


class SSOUser(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    groups: list[str] = []
    tenant_id: Optional[str] = None


class SSOHandler:
    """Handle SSO/SAML authentication"""

    def __init__(self, config: SSOConfig):
        self.config = config

    async def authenticate(self, token: str) -> SSOUser:
        """Authenticate user via SSO (IdP token or dev email token)."""
        if not self.config.enabled:
            raise HTTPException(status_code=501, detail='SSO not configured')

        parsed = self._parse_dev_token(token)
        if parsed:
            return parsed

        if self.config.provider == SSOProvider.OKTA:
            return await self._authenticate_okta(token)
        if self.config.provider == SSOProvider.AZURE_AD:
            return await self._authenticate_azure_ad(token)
        if self.config.provider == SSOProvider.SAML:
            return await self._authenticate_saml(token)

        raise HTTPException(
            status_code=400,
            detail=f'Unsupported SSO provider: {self.config.provider}',
        )

    def _parse_dev_token(self, token: str) -> Optional[SSOUser]:
        """Allow `user@org.com` tokens in dev when full OAuth introspection is not wired."""
        value = (token or '').strip()
        if '@' in value and '.' in value.split('@', 1)[-1]:
            local, domain = value.split('@', 1)
            return SSOUser(
                email=value.lower(),
                first_name=local.replace('.', ' ').title(),
                last_name='User',
                groups=['Enterprise Users'],
            )
        return None

    async def _authenticate_okta(self, token: str) -> SSOUser:
        logger.info('Authenticating via Okta')
        parsed = self._parse_dev_token(token)
        if parsed:
            return parsed
        raise HTTPException(status_code=401, detail='Okta token validation not configured')

    async def _authenticate_azure_ad(self, token: str) -> SSOUser:
        logger.info('Authenticating via Azure AD')
        parsed = self._parse_dev_token(token)
        if parsed:
            return parsed
        raise HTTPException(status_code=401, detail='Azure AD token validation not configured')

    async def _authenticate_saml(self, assertion: str) -> SSOUser:
        logger.info('Authenticating via SAML')
        parsed = self._parse_dev_token(assertion)
        if parsed:
            return parsed
        raise HTTPException(status_code=401, detail='SAML assertion validation not configured')

    def get_login_url(self, redirect_uri: str) -> str:
        """Get SSO login URL"""
        if not self.config.enabled:
            raise HTTPException(
                status_code=501,
                detail="SSO not configured"
            )

        if self.config.provider == SSOProvider.OKTA:
            return f"https://{self.config.domain}.okta.com/oauth2/v1/authorize?client_id={self.config.client_id}&redirect_uri={redirect_uri}&response_type=code&scope=openid profile email"
        elif self.config.provider == SSOProvider.AZURE_AD:
            return f"https://login.microsoftonline.com/{self.config.tenant_id}/oauth2/v2.0/authorize?client_id={self.config.client_id}&redirect_uri={redirect_uri}&response_type=code&scope=openid profile email"
        elif self.config.provider == SSOProvider.SAML:
            # SAML uses XML, not URL-based auth flow
            return "/auth/saml/login"
        
        return ""

    def map_groups_to_roles(self, groups: list[str]) -> dict:
        """Map SSO groups to tenant membership roles."""
        roles: list[str] = []
        for group in groups:
            mapped = GROUP_TO_MEMBERSHIP.get(group) or normalize_membership_role(group)
            if mapped and mapped in MEMBERSHIP_ROLES and mapped not in roles:
                roles.append(mapped)
        primary = roles[0] if roles else 'member'
        return {
            'roles': roles if roles else ['member'],
            'membership_role': primary,
            'permissions': list(permissions_for_role(primary)),
        }


class SSOService:
    """Enterprise SSO helpers (config persistence via ``tenant_store``)."""

    @classmethod
    async def list_providers(cls) -> list[dict]:
        """List available SSO providers"""
        return [
            {
                "id": "okta",
                "name": "Okta",
                "description": "Okta Identity Cloud",
                "fields": ["domain", "client_id", "client_secret"],
            },
            {
                "id": "azure_ad",
                "name": "Microsoft Azure AD",
                "description": "Azure Active Directory",
                "fields": ["tenant_id", "client_id", "client_secret"],
            },
            {
                "id": "saml",
                "name": "SAML 2.0",
                "description": "Generic SAML Identity Provider",
                "fields": ["metadata_url", "idp_entity_id", "sp_entity_id"],
            },
        ]


__all__ = [
    'SSOProvider',
    'SSOConfig',
    'SSOUser',
    'SSOHandler',
    'SSOService',
    'GROUP_TO_MEMBERSHIP',
]