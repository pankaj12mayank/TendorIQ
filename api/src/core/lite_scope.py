"""User-scoped query helpers for TenderIQ Lite (Phase 1)."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Select, or_

from .auth import AuthContext


def parse_user_uuid(user_id: str) -> UUID:
    return UUID(str(user_id))


def user_owns_row(row: Any, user_id: str) -> bool:
    """True if row belongs to the user (owner_id or legacy created_by_id)."""
    uid = str(user_id)
    owner = getattr(row, 'owner_id', None)
    if owner is not None and str(owner) == uid:
        return True
    created = getattr(row, 'created_by_id', None)
    if created is not None and str(created) == uid:
        return True
    bidder = getattr(row, 'bidder_id', None)
    if bidder is not None and str(bidder) == uid:
        return True
    return False


def apply_user_scope(
    query: Select,
    model: type,
    auth: AuthContext,
    *,
    include_tenant_fallback: bool = True,
) -> Select:
    """Restrict query to the current user's data (super_admin sees all)."""
    if auth.is_super_admin():
        return query

    uid = parse_user_uuid(auth.user_id)
    clauses = []
    if hasattr(model, 'owner_id'):
        clauses.append(model.owner_id == uid)
    if hasattr(model, 'created_by_id'):
        clauses.append(model.created_by_id == uid)
    if hasattr(model, 'bidder_id'):
        clauses.append(model.bidder_id == uid)

    if not clauses:
        return query

    scoped = or_(*clauses)
    if include_tenant_fallback and auth.tenant_id and hasattr(model, 'tenant_id'):
        scoped = or_(scoped, model.tenant_id == parse_user_uuid(auth.tenant_id))
    return query.where(scoped)


def owner_filter_dict(auth: AuthContext) -> dict[str, Any]:
    """Repository-style filter dict for list endpoints."""
    if auth.is_super_admin():
        return {}
    return {'owner_id': str(auth.user_id)}
