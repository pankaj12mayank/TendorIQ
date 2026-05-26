"""Resolve AuthContext from bearer tokens (JWT + optional Clerk)."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .auth import AuthService, AuthContext, ClerkAuthService
from .clerk_bootstrap import resolve_clerk_auth_context
from .config import settings
from .supabase_auth import verify_supabase_access_token
from .supabase_bootstrap import resolve_supabase_auth_context
from .roles import normalize_membership_role, is_platform_super_admin, PLATFORM_ROLE_SUPER_ADMIN


def _clerk_email_from_api(clerk_user: dict) -> Optional[str]:
    addresses = clerk_user.get('email_addresses') or []
    if isinstance(addresses, list) and addresses:
        first = addresses[0]
        if isinstance(first, dict):
            return first.get('email_address')
    return None


async def resolve_auth_from_token(
    token: str,
    db: AsyncSession,
) -> Optional[AuthContext]:
    """Build AuthContext from a bearer token (shared by middleware and Depends)."""
    supabase_claims = verify_supabase_access_token(token)
    if supabase_claims:
        resolved = await resolve_supabase_auth_context(db, supabase_claims)
        if resolved:
            user_id, email, tenant_id, membership_role, _name = resolved
            return AuthContext(
                user_id=user_id,
                email=email,
                role=membership_role,
                tenant_id=tenant_id,
                membership_role=membership_role,
            )

    clerk_key = settings.CLERK_SECRET_KEY or ''
    clerk_ready = (
        settings.AUTH_PROVIDER == 'clerk'
        and clerk_key
        and 'placeholder' not in clerk_key.lower()
        and len(clerk_key) > 20
    )

    if clerk_ready:
        clerk_user = await ClerkAuthService.verify_token(token)
        if clerk_user:
            resolved = await resolve_clerk_auth_context(db, clerk_user)
            if resolved:
                user_id, email, tenant_id, membership_role, _name = resolved
                return AuthContext(
                    user_id=user_id,
                    email=email,
                    role=membership_role,
                    tenant_id=tenant_id,
                    membership_role=membership_role,
                )
            metadata = clerk_user.get('public_metadata') or {}
            fallback_role = normalize_membership_role(
                metadata.get('membership_role') or metadata.get('role')
            ) or 'member'
            return AuthContext(
                user_id=clerk_user.get('id', ''),
                email=_clerk_email_from_api(clerk_user),
                role=fallback_role,
                membership_role=fallback_role,
            )

    auth_service = AuthService()
    token_payload = auth_service.verify_token(token)
    if not token_payload:
        return None

    membership_role = token_payload.membership_role or normalize_membership_role(
        token_payload.role
    )
    platform_role = (
        PLATFORM_ROLE_SUPER_ADMIN
        if is_platform_super_admin(token_payload.role)
        else token_payload.role
    )
    return AuthContext(
        user_id=token_payload.sub,
        email=token_payload.email,
        role=platform_role,
        tenant_id=token_payload.tenant_id,
        membership_role=membership_role,
    )
