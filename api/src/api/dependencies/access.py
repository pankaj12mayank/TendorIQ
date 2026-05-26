"""Lightweight auth dependencies for TenderIQ Lite."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import AuthContext
from ...core.database import get_db
from ...core.personal_workspace import ensure_personal_workspace
from .auth import get_current_user


async def require_authenticated(
    auth: AuthContext = Depends(get_current_user),
) -> AuthContext:
    return auth


async def require_lite_user(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Authenticated user with personal workspace (user-scoped Lite MVP)."""
    if auth.is_super_admin():
        return auth
    if not auth.tenant_id:
        tenant_id, membership_role = await ensure_personal_workspace(
            db,
            auth.user_id,
            auth.email,
        )
        auth.tenant_id = tenant_id
        if not auth.membership_role:
            auth.membership_role = membership_role
    return auth


async def require_tenant_member(
    auth: AuthContext = Depends(require_lite_user),
) -> AuthContext:
    """Backward-compatible alias — Lite uses personal workspace, not shared org picker."""
    if not auth.tenant_id and not auth.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Workspace context required',
        )
    return auth


CurrentUser = Annotated[AuthContext, Depends(require_authenticated)]
LiteUser = Annotated[AuthContext, Depends(require_lite_user)]
TenantUser = Annotated[AuthContext, Depends(require_tenant_member)]
