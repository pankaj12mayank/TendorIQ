"""Add revoked_tokens table for DB-backed JWT revocation.

Revision ID: 20260529_revoked_tokens
Revises: 20260527_retire_supabase_id
"""

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import create_index_if_missing, table_exists  # noqa: E402

revision = '20260529_revoked_tokens'
down_revision = '20260527_retire_supabase_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists('revoked_tokens'):
        return
    op.create_table(
        'revoked_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti', name='uq_revoked_jti'),
    )
    create_index_if_missing('idx_revoked_jti', 'revoked_tokens', ['jti'])


def downgrade() -> None:
    op.drop_table('revoked_tokens')
