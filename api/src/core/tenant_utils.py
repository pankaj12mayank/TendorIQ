"""Tenant ID helpers for routes and services."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import AuthContext
from .models import pk_str


def parse_tenant_uuid(tenant_id: Optional[str]) -> UUID:
    """Parse tenant id or raise 400 (avoids 500 from bare UUID())."""
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant context required',
        )
    try:
        return UUID(str(tenant_id))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid tenant ID',
        ) from exc


async def resolve_member_tenant_uuid(
    auth: AuthContext,
    db: AsyncSession,
) -> UUID:
    """Customer workspace tenant (regular users + owner test mode)."""
    if not auth.tenant_id:
        from .personal_workspace import ensure_personal_workspace

        tenant_id, membership_role = await ensure_personal_workspace(
            db,
            auth.user_id,
            auth.email,
        )
        auth.tenant_id = tenant_id
        if membership_role and not auth.membership_role:
            auth.membership_role = membership_role
    return parse_tenant_uuid(auth.tenant_id)


async def load_tenant_for_member(
    auth: AuthContext,
    db: AsyncSession,
):
    """Load tenant row for billing/access checks (SQLite-safe PK)."""
    from .models import Tenant

    tenant_uuid = await resolve_member_tenant_uuid(auth, db)
    tenant = await db.get(Tenant, pk_str(tenant_uuid))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Workspace not found')
    return tenant, tenant_uuid


def effective_tenant_id(auth: AuthContext, request_tenant_id: Optional[str] = None) -> str:
    """Prefer middleware-bound tenant, then JWT membership tenant."""
    tid = request_tenant_id or auth.tenant_id
    if not tid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant context required',
        )
    return str(tid)
