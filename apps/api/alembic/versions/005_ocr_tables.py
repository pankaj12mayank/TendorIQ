"""Add OCR results and jobs tables

Revision ID: 005_ocr_tables
Revises: 004_document_processing
Create Date: 2024-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '005_ocr_tables'
down_revision: Union[str, None] = '004_document_processing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ocr_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('word_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('language', sa.String(10), nullable=True, server_default='en'),
        sa.Column('is_low_quality', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('blur_score', sa.Float(), nullable=True),
        sa.Column('brightness_score', sa.Float(), nullable=True),
        sa.Column('contrast_score', sa.Float(), nullable=True),
        sa.Column('overall_quality_score', sa.Float(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ocr_document', 'ocr_results', ['document_id'])
    op.create_index('idx_ocr_tenant_created', 'ocr_results', ['tenant_id', 'created_at'])
    op.create_index('idx_ocr_status', 'ocr_results', ['status'])
    op.create_index('idx_ocr_confidence', 'ocr_results', ['confidence_score'])

    op.create_table('ocr_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('arq_job_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('result_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('arq_job_id')
    )
    op.create_index('idx_ocrjob_document', 'ocr_jobs', ['document_id'])
    op.create_index('idx_ocrjob_status', 'ocr_jobs', ['status'])
    op.create_index('idx_ocrjob_arq', 'ocr_jobs', ['arq_job_id'])


def downgrade() -> None:
    op.drop_index('idx_ocrjob_arq', table_name='ocr_jobs')
    op.drop_index('idx_ocrjob_status', table_name='ocr_jobs')
    op.drop_index('idx_ocrjob_document', table_name='ocr_jobs')
    op.drop_table('ocr_jobs')

    op.drop_index('idx_ocr_confidence', table_name='ocr_results')
    op.drop_index('idx_ocr_status', table_name='ocr_results')
    op.drop_index('idx_ocr_tenant_created', table_name='ocr_results')
    op.drop_index('idx_ocr_document', table_name='ocr_results')
    op.drop_table('ocr_results')