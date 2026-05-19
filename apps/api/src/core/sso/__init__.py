"""SSO/SAML Integration for Enterprise Authentication"""

import logging
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


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
        """Authenticate user via SSO"""
        if not self.config.enabled:
            raise HTTPException(
                status_code=501,
                detail="SSO not configured"
            )

        if self.config.provider == SSOProvider.OKTA:
            return await self._authenticate_okta(token)
        elif self.config.provider == SSOProvider.AZURE_AD:
            return await self._authenticate_azure_ad(token)
        elif self.config.provider == SSOProvider.SAML:
            return await self._authenticate_saml(token)
        
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported SSO provider: {self.config.provider}"
        )

    async def _authenticate_okta(self, token: str) -> SSOUser:
        """Authenticate via Okta"""
        # In production, this would call Okta's API
        # Example: GET https://{domain}.okta.com/api/v1/users/me
        logger.info("Authenticating via Okta")
        
        # Stub for demo
        return SSOUser(
            email="user@company.com",
            first_name="John",
            last_name="Doe",
            groups=["Admins"],
        )

    async def _authenticate_azure_ad(self, token: str) -> SSOUser:
        """Authenticate via Azure AD"""
        # In production, this would call Microsoft Graph API
        # Example: GET https://graph.microsoft.com/v1.0/me
        logger.info("Authenticating via Azure AD")
        
        # Stub for demo
        return SSOUser(
            email="user@company.com",
            first_name="John",
            last_name="Doe",
            groups=["Enterprise Users"],
        )

    async def _authenticate_saml(self, assertion: str) -> SSOUser:
        """Authenticate via SAML assertion"""
        # In production, this would parse SAML response
        # Use python3-saml or onelogin-saml
        logger.info("Authenticating via SAML")
        
        # Stub for demo
        return SSOUser(
            email="user@company.com",
            first_name="John",
            last_name="Doe",
            groups=["SSO Users"],
        )

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
        """Map SSO groups to TenderIQ roles"""
        # Configure group mappings per tenant
        role_mappings = {
            'Admins': 'admin',
            'Managers': 'manager',
            'Analysts': 'analyst',
            'Viewers': 'viewer',
            'Enterprise Users': 'manager',
        }
        
        roles = []
        for group in groups:
            if role := role_mappings.get(group):
                roles.append(role)
        
        # Default to viewer if no mapping
        return {
            'roles': roles if roles else ['viewer'],
            'permissions': self._get_permissions_from_roles(roles if roles else ['viewer'])
        }

    def _get_permissions_from_roles(self, roles: list[str]) -> list[str]:
        """Get permissions based on roles"""
        # Map roles to permissions
        all_permissions = {
            'admin': ['all'],
            'manager': ['read', 'write', 'tender:create', 'document:upload', 'export'],
            'analyst': ['read', 'tender:create', 'document:upload'],
            'viewer': ['read'],
        }
        
        permissions = set()
        for role in roles:
            if perms := all_permissions.get(role):
                permissions.update(perms)
        
        return list(permissions)


class SSOService:
    """Enterprise SSO management"""

    _configs: dict[str, SSOConfig] = {}

    @classmethod
    async def configure(cls, tenant_id: str, config: SSOConfig) -> dict:
        """Configure SSO for a tenant"""
        cls._configs[tenant_id] = config
        logger.info(f"SSO configured for tenant {tenant_id}: {config.provider}")
        return {"success": True, "provider": config.provider}

    @classmethod
    async def get_config(cls, tenant_id: str) -> Optional[SSOConfig]:
        """Get SSO configuration for tenant"""
        return cls._configs.get(tenant_id)

    @classmethod
    async def authenticate(cls, tenant_id: str, token: str) -> SSOUser:
        """Authenticate user with SSO"""
        config = cls._configs.get(tenant_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail="SSO not configured for this organization"
            )
        
        handler = SSOHandler(config)
        return await handler.authenticate(token)

    @classmethod
    async def get_login_url(cls, tenant_id: str, redirect_uri: str) -> str:
        """Get SSO login URL for tenant"""
        config = cls._configs.get(tenant_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail="SSO not configured for this organization"
            )
        
        handler = SSOHandler(config)
        return handler.get_login_url(redirect_uri)

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


__all__ = ['SSOProvider', 'SSOConfig', 'SSOUser', 'SSOHandler', 'SSOService']