"""SQLite: add columns that phase1/2 skipped on sqlite dialect.

Revision ID: 20260526_sqlite_schema
Revises: 20260525_phase10_cleanup
"""

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import add_column_if_missing  # noqa: E402

revision = '20260526_sqlite_schema'
down_revision = '20260525_phase10_cleanup'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        return

    add_column_if_missing(
        'users',
        sa.Column('supabase_id', sa.String(255), nullable=True),
    )
    add_column_if_missing(
        'tenants',
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    add_column_if_missing(
        'proposals',
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    add_column_if_missing(
        'tenders',
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    add_column_if_missing(
        'documents',
        sa.Column('owner_id', sa.String(36), nullable=True),
    )


def downgrade() -> None:
    pass
