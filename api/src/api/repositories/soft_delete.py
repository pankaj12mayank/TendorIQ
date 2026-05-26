"""Helpers for models using ``SoftDeleteMixin`` (``deleted_at`` column)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select


def model_has_soft_delete(model: type[Any]) -> bool:
    return hasattr(model, 'deleted_at')


def apply_active_only(query: Select, model: type[Any]) -> Select:
    if model_has_soft_delete(model):
        return query.where(model.deleted_at.is_(None))
    return query


def mark_soft_deleted(instance: Any) -> None:
    instance.deleted_at = datetime.now(timezone.utc)
