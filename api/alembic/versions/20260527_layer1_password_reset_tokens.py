"""Layer1: add password_reset_tokens table.

Revision ID: 20260527_layer1_password_reset
Revises: 20260526_sqlite_schema
"""

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import create_index_if_missing, table_exists  # noqa: E402

revision = '20260527_layer1_password_reset'
down_revision = '20260526_sqlite_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists('password_reset_tokens'):
        return
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requested_ip', sa.String(length=45), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    create_index_if_missing('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    create_index_if_missing('ix_password_reset_tokens_token_hash', 'password_reset_tokens', ['token_hash'])
    create_index_if_missing('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])
    create_index_if_missing(
        'idx_password_reset_user_active',
        'password_reset_tokens',
        ['user_id', 'expires_at', 'used_at'],
    )


def downgrade() -> None:
    op.drop_index('idx_password_reset_user_active', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_token_hash', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
