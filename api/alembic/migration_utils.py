"""Idempotent helpers for Alembic upgrades (safe re-run on partially migrated DBs)."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


def _insp():
    return inspect(op.get_bind())


def table_exists(name: str) -> bool:
    return name in _insp().get_table_names()


def column_exists(table: str, column: str) -> bool:
    if not table_exists(table):
        return False
    return column in {c['name'] for c in _insp().get_columns(table)}


def index_exists(table: str, index_name: str) -> bool:
    if not table_exists(table):
        return False
    return index_name in {idx['name'] for idx in _insp().get_indexes(table)}


def add_column_if_missing(table: str, column: sa.Column) -> None:
    if not column_exists(table, column.name):
        op.add_column(table, column)


def create_index_if_missing(name: str, table: str, columns: list[str], **kw) -> None:
    if not index_exists(table, name):
        op.create_index(name, table, columns, **kw)


def drop_index_if_exists(name: str, table: str) -> None:
    if index_exists(table, name):
        op.drop_index(name, table_name=table)
