"""Add AIProvider and DismissedFailedJob models

Revision ID: 20260522_admin_store
Revises:
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20260522_admin_store'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_providers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('provider_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('provider_type', sa.String(50), nullable=False, server_default='ollama'),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('api_key_enc', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('TRUE')),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default=sa.text('FALSE')),
        sa.Column('models', mysql.JSON, nullable=False, server_default='[]'),
        sa.Column('settings', mysql.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # Add MySQL ON UPDATE CURRENT_TIMESTAMP for updated_at
    op.execute(
        "ALTER TABLE ai_providers MODIFY COLUMN updated_at DATETIME "
        "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    )

    op.create_table(
        'dismissed_failed_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )


def downgrade() -> None:
    op.drop_table('dismissed_failed_jobs')
    op.drop_table('ai_providers')
