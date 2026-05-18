"""Add parsed documents and chunking tables

Revision ID: 006_parsing_tables
Revises: 005_ocr_tables
Create Date: 2024-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006_parsing_tables'
down_revision: Union[str, None] = '005_ocr_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('parsed_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('word_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('confidence_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('sections_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tables_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('images_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('links_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('chunking_strategy', sa.String(20), nullable=True, server_default='hybrid'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_parsed_document', 'parsed_documents', ['document_id'])
    op.create_index('idx_parsed_status', 'parsed_documents', ['status'])

    op.alter_column('document_chunks', 'content',
        existing_type=sa.Text(),
        nullable=True)

    op.add_column('document_chunks', sa.Column('parsed_document_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('document_chunks', sa.Column('start_page', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('document_chunks', sa.Column('end_page', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('document_chunks', sa.Column('section_path', sa.String(500), nullable=True))
    op.add_column('document_chunks', sa.Column('tokens', sa.Integer(), nullable=True, server_default='0'))

    op.drop_index('idx_chunk_document', table_name='document_chunks')
    op.create_index('idx_chunk_document', 'document_chunks', ['document_id'])
    op.create_index('idx_chunk_parsed', 'document_chunks', ['parsed_document_id'])

    op.create_unique_constraint('unique_chunk_order', 'document_chunks', ['document_id', 'chunk_index'])


def downgrade() -> None:
    op.drop_constraint('unique_chunk_order', 'document_chunks', type_='unique')
    op.drop_index('idx_chunk_parsed', table_name='document_chunks')
    op.drop_index('idx_chunk_document', table_name='document_chunks')

    op.drop_column('document_chunks', 'tokens')
    op.drop_column('document_chunks', 'section_path')
    op.drop_column('document_chunks', 'end_page')
    op.drop_column('document_chunks', 'start_page')
    op.drop_column('document_chunks', 'parsed_document_id')

    op.drop_index('idx_parsed_status', table_name='parsed_documents')
    op.drop_index('idx_parsed_document', table_name='parsed_documents')
    op.drop_table('parsed_documents')