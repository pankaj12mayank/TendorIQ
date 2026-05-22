"""Layer 1 — DB refinements: indexes, constraints, billing_cycle, relationships

Revision ID: 20260522_layer1_db_refinements
Revises: 20260522_admin_store
Create Date: 2026-05-22 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260522_layer1_db_refinements'
down_revision: Union[str, None] = '20260522_admin_store'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Tenant: add billing_cycle + plan index ---
    op.add_column('tenants', sa.Column('billing_cycle', sa.String(20), server_default='monthly', nullable=False))
    op.create_index('idx_tenant_plan', 'tenants', ['plan'])

    # --- User: add email_verified index, expand role constraint ---
    op.create_index('idx_user_email_verified', 'users', ['email_verified'])
    op.drop_constraint('valid_user_role', 'users', type_='check')
    op.create_check_constraint(
        'valid_user_role',
        'users',
        sa.text("role IN ('owner', 'admin', 'manager', 'analyst', 'member', 'viewer')"),
    )

    # --- Membership: expand role constraint ---
    op.drop_constraint('valid_membership_role', 'memberships', type_='check')
    op.create_check_constraint(
        'valid_membership_role',
        'memberships',
        sa.text("role IN ('owner', 'admin', 'manager', 'analyst', 'member', 'viewer')"),
    )

    # --- Bid: tenant-scoped indexes ---
    op.create_index('idx_bid_tenant_tender', 'bids', ['tenant_id', 'tender_id'])
    op.create_index('idx_bid_tenant_status', 'bids', ['tenant_id', 'status'])

    # --- Proposal: indexes ---
    op.create_index('idx_proposal_bidder', 'proposals', ['bidder_id'])
    op.create_index('idx_proposal_tenant', 'proposals', ['tenant_id'])
    op.create_index('idx_proposal_tenant_tender', 'proposals', ['tenant_id', 'tender_id'])

    # --- Subscription: tenant-scoped indexes ---
    op.create_index('idx_sub_tenant_plan', 'subscriptions', ['tenant_id', 'plan'])
    op.create_index('idx_sub_tenant_status', 'subscriptions', ['tenant_id', 'status'])

    # --- Notification: user + tenant created-at indexes ---
    op.create_index('idx_notification_user_created', 'notifications', ['user_id', 'created_at'])
    op.create_index('idx_notification_tenant_created', 'notifications', ['tenant_id', 'created_at'])

    # --- UsageLog: resource composite index ---
    op.create_index('idx_usage_resource', 'usage_logs', ['resource_type', 'resource_id'])

    # --- QueueJob: tenant-scoped status index ---
    op.create_index('idx_job_tenant_status', 'queue_jobs', ['tenant_id', 'status'])

    # --- AIProvider: type index ---
    op.create_index('idx_ai_provider_type', 'ai_providers', ['provider_type'])


def downgrade() -> None:
    op.drop_index('idx_ai_provider_type', table_name='ai_providers')
    op.drop_index('idx_job_tenant_status', table_name='queue_jobs')
    op.drop_index('idx_usage_resource', table_name='usage_logs')
    op.drop_index('idx_notification_tenant_created', table_name='notifications')
    op.drop_index('idx_notification_user_created', table_name='notifications')
    op.drop_index('idx_sub_tenant_status', table_name='subscriptions')
    op.drop_index('idx_sub_tenant_plan', table_name='subscriptions')
    op.drop_index('idx_proposal_tenant_tender', table_name='proposals')
    op.drop_index('idx_proposal_tenant', table_name='proposals')
    op.drop_index('idx_proposal_bidder', table_name='proposals')
    op.drop_index('idx_bid_tenant_status', table_name='bids')
    op.drop_index('idx_bid_tenant_tender', table_name='bids')

    op.drop_constraint('valid_membership_role', 'memberships', type_='check')
    op.create_check_constraint(
        'valid_membership_role',
        'memberships',
        sa.text("role IN ('owner', 'admin', 'member', 'viewer')"),
    )

    op.drop_constraint('valid_user_role', 'users', type_='check')
    op.create_check_constraint(
        'valid_user_role',
        'users',
        sa.text("role IN ('owner', 'admin', 'member', 'viewer')"),
    )
    op.drop_index('idx_user_email_verified', table_name='users')

    op.drop_index('idx_tenant_plan', table_name='tenants')
    op.drop_column('tenants', 'billing_cycle')
