"""Normalize users.preferences / JSON columns (SQLite may return str)."""

from __future__ import annotations

import json
from typing import Any


def normalize_preferences(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return {}
