"""Add storage and lifecycle fields to documents

Revision ID: 003_document_storage_fields
Revises: 002_onboarding_states
Create Date: 2024-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003_document_storage_fields'
down_revision: Union[str, None] = '002_onboarding_states'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('storage_path', sa.String(2000), nullable=True))
    op.add_column('documents', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('documents', sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('documents', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('documents', sa.Column('access_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('documents', sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_document_expires', 'documents', ['expires_at'])
    op.create_index('idx_document_archived', 'documents', ['is_archived'])


def downgrade() -> None:
    op.drop_index('idx_document_archived', table_name='documents')
    op.drop_index('idx_document_expires', table_name='documents')
    op.drop_column('documents', 'last_accessed_at')
    op.drop_column('documents', 'access_count')
    op.drop_column('documents', 'archived_at')
    op.drop_column('documents', 'is_archived')
    op.drop_column('documents', 'expires_at')
    op.drop_column('documents', 'storage_path')