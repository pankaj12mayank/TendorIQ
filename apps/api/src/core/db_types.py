"""Database column types compatible with MySQL and PostgreSQL."""

from sqlalchemy import JSON, String

# UUIDs stored as CHAR(36) — works on MySQL, MariaDB, PostgreSQL, SQLite
UuidCol = String(36)

# JSON columns (MySQL 5.7+ native JSON)
JsonCol = JSON
