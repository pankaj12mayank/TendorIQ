"""Add Prompt Management Tables

Revision ID: 007_prompt_management
Revises: 006_parsing_tables
Create Date: 2024-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '007_prompt_management'
down_revision: Union[str, None] = '006_parsing_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('prompt_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prompt_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prompt_name', 'prompt_templates', ['name'])
    op.create_index('idx_prompt_type', 'prompt_templates', ['prompt_type'])
    op.create_index('idx_prompt_tenant', 'prompt_templates', ['tenant_id'])
    op.create_index('idx_prompt_active', 'prompt_templates', ['is_active'])

    op.create_table('prompt_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('system_message', sa.Text(), nullable=True),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('guardrails', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('examples', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer(), nullable=True, server_default='2048'),
        sa.Column('top_p', sa.Float(), nullable=True),
        sa.Column('frequency_penalty', sa.Float(), nullable=True),
        sa.Column('presence_penalty', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompt_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prompt_id', 'version', name='unique_prompt_version')
    )
    op.create_index('idx_pv_prompt', 'prompt_versions', ['prompt_id'])
    op.create_index('idx_pv_active', 'prompt_versions', ['is_active'])

    op.create_table('prompt_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_input_tokens', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('total_output_tokens', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=6), nullable=True, server_default='0'),
        sa.Column('avg_latency_ms', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_confidence', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('avg_user_rating', sa.Float(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompt_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['prompt_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prompt_id', 'version_id', 'tenant_id', name='unique_prompt_version_tenant')
    )
    op.create_index('idx_pa_prompt', 'prompt_analytics', ['prompt_id'])
    op.create_index('idx_pa_tenant', 'prompt_analytics', ['tenant_id'])

    op.create_table('prompt_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('actor', sa.String(255), nullable=True),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompt_templates.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['version_id'], ['prompt_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pal_prompt', 'prompt_audit_log', ['prompt_id'])
    op.create_index('idx_pal_action', 'prompt_audit_log', ['action'])
    op.create_index('idx_pal_actor', 'prompt_audit_log', ['actor'])
    op.create_index('idx_pal_created', 'prompt_audit_log', ['created_at'])


def downgrade() -> None:
    op.drop_table('prompt_audit_log')
    op.drop_table('prompt_analytics')
    op.drop_table('prompt_versions')
    op.drop_table('prompt_templates')