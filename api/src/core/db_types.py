"""Database column types compatible with MySQL, PostgreSQL, and SQLite."""

from sqlalchemy import JSON, String
from sqlalchemy.types import TypeDecorator


class _UUIDString(TypeDecorator):
    """UUIDs stored as CHAR(36) — auto-converts UUID objects to strings for SQLite compat."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        return value


# UUIDs stored as CHAR(36) — works on MySQL, MariaDB, PostgreSQL, SQLite
UuidCol = _UUIDString

# JSON columns (MySQL 5.7+ native JSON)
JsonCol = JSON
