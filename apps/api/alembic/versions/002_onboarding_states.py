"""Add onboarding_states table

Revision ID: 002_onboarding_states
Revises: 001_initial
Create Date: 2024-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002_onboarding_states'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('onboarding_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('total_steps', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('step_1_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('step_2_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('step_3_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('step_4_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('step_5_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('step_1_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('step_2_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('step_3_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('step_4_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('step_5_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_step_completed', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_onboarding_user', 'onboarding_states', ['user_id'])
    op.create_index('idx_onboarding_tenant', 'onboarding_states', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('idx_onboarding_tenant', table_name='onboarding_states')
    op.drop_index('idx_onboarding_user', table_name='onboarding_states')
    op.drop_table('onboarding_states')