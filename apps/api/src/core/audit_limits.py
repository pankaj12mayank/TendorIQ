"""Shared limits for audit list and export endpoints."""

DEFAULT_AUDIT_LIST_LIMIT = 100
MAX_AUDIT_LIST_LIMIT = 500
MAX_AUDIT_EXPORT_ROWS = 5000


def clamp_export_limit(limit: int | None) -> int:
    """Cap export row count to protect DB and response size."""
    if limit is None:
        return MAX_AUDIT_EXPORT_ROWS
    return max(1, min(int(limit), MAX_AUDIT_EXPORT_ROWS))
