"""Phase 2: Supabase user id column.

Revision ID: 20260525_phase2_supabase
Revises: 20260525_phase1_user
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa

revision = '20260525_phase2_supabase'
down_revision = '20260525_phase1_user'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # Applied in 20260526_sqlite_lite_schema_columns (idempotent).
        return
    op.add_column('users', sa.Column('supabase_id', sa.String(255), nullable=True))
    op.create_index('idx_users_supabase_id', 'users', ['supabase_id'], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        return
    op.drop_index('idx_users_supabase_id', table_name='users')
    op.drop_column('users', 'supabase_id')
