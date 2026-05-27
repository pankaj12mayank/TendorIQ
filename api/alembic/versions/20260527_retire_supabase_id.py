"""Retire users.supabase_id (SQLite-safe, idempotent).

Revision ID: 20260527_retire_supabase_id
Revises: 20260527_layer2_payment_transactions
"""

from __future__ import annotations

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import (  # noqa: E402
    column_exists,
    drop_column_if_exists,
    drop_index_if_exists,
)

revision = '20260527_retire_supabase_id'
down_revision = '20260527_layer2_payment_transactions'
branch_labels = None
depends_on = None

_SUPABASE_INDEX_NAMES = (
    'idx_users_supabase_id',
    'ix_users_supabase_id',
)


def upgrade() -> None:
    if not column_exists('users', 'supabase_id'):
        for name in _SUPABASE_INDEX_NAMES:
            drop_index_if_exists(name, 'users')
        return

    for name in _SUPABASE_INDEX_NAMES:
        drop_index_if_exists(name, 'users')

    drop_column_if_exists('users', 'supabase_id')


def downgrade() -> None:
    if column_exists('users', 'supabase_id'):
        return

    bind = op.get_bind()
    col = sa.Column('supabase_id', sa.String(255), nullable=True)
    if bind.dialect.name == 'sqlite':
        with op.batch_alter_table('users') as batch_op:
            batch_op.add_column(col)
    else:
        op.add_column('users', col)
        op.create_index('idx_users_supabase_id', 'users', ['supabase_id'], unique=True)
