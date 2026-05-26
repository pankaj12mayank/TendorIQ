"""Typed aliases for tenant-scoped identifiers (documentation + optional static checking)."""

from typing import TypeAlias
from uuid import UUID

TenantId: TypeAlias = str
UserId: TypeAlias = str


def parse_tenant_uuid(tenant_id: TenantId | str | None) -> UUID:
    """Parse tenant id for DB queries; raises ValueError when missing or invalid."""
    if not tenant_id:
        raise ValueError('tenant_id is required')
    return UUID(str(tenant_id))
