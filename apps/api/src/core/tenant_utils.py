"""Tenant ID helpers for routes and services."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from .auth import AuthContext


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


def effective_tenant_id(auth: AuthContext, request_tenant_id: Optional[str] = None) -> str:
    """Prefer middleware-bound tenant, then JWT membership tenant."""
    tid = request_tenant_id or auth.tenant_id
    if not tid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Tenant context required',
        )
    return str(tid)
