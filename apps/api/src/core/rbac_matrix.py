"""Load canonical role → permissions matrix from packages/shared/permissions.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

T = TypeVar('T')

_MATRIX_PATH = (
    Path(__file__).resolve().parents[4] / 'packages' / 'shared' / 'permissions.json'
)

# Legacy UI names → API permission string values
PERMISSION_ALIASES: dict[str, str] = {
    'tender:write': 'tender:update',
    'bid:write': 'bid:update',
    'document:write': 'document:create',
    'org:write': 'org:update',
    'settings:write': 'settings:update',
}


def load_role_permissions_matrix(permission_enum: type[T]) -> dict[str, set[T]]:
    with _MATRIX_PATH.open(encoding='utf-8') as f:
        raw: dict[str, list[str]] = json.load(f)
    return {
        role: {permission_enum(value) for value in values}
        for role, values in raw.items()
    }


def coerce_permission_value(permission_enum: type[T], permission: T | str) -> T | None:
    if isinstance(permission, permission_enum):
        return permission
    key = PERMISSION_ALIASES.get(str(permission), str(permission))
    try:
        return permission_enum(key)
    except ValueError:
        return None
