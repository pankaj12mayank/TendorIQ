"""Add processing status and document management fields

Revision ID: 004_document_processing
Revises: 003_document_storage_fields
Create Date: 2024-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004_document_processing'
down_revision: Union[str, None] = '003_document_storage_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('documents', sa.Column('processing_status', sa.String(30), nullable=True, server_default='uploaded'))
    op.add_column('documents', sa.Column('processing_error', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('documents', sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'))
    op.add_column('documents', sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('documents', sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('documents', sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))

    op.create_index('idx_document_status', 'documents', ['processing_status'])
    op.create_index('idx_document_tenant_status', 'documents', ['tenant_id', 'processing_status'])
    op.create_index('idx_document_folder', 'documents', ['folder'])

    op.alter_column('documents', 'file_size',
        existing_type=sa.Integer(),
        nullable=False,
        existing_server_default=sa.text('0'))

    op.create_check_constraint(
        'valid_processing_status',
        'documents',
        "processing_status IN ('uploaded', 'processing', 'retrying', 'completed', 'failed', 'needs_review', 'deleted')"
    )


def downgrade() -> None:
    op.drop_constraint('valid_processing_status', 'documents', type_='check')
    op.drop_index('idx_document_folder', table_name='documents')
    op.drop_index('idx_document_tenant_status', table_name='documents')
    op.drop_index('idx_document_status', table_name='documents')
    op.drop_column('documents', 'processed_at')
    op.drop_column('documents', 'uploaded_at')
    op.drop_column('documents', 'tags')
    op.drop_column('documents', 'max_retries')
    op.drop_column('documents', 'retry_count')
    op.drop_column('documents', 'processing_error')
    op.drop_column('documents', 'processing_status')
    op.drop_column('documents', 'category')