"""Layer 1 — DB refinements: indexes, constraints (idempotent).

Revision ID: 20260522_layer1_db_refinements
Revises: 20260522_admin_store
Create Date: 2026-05-22 00:00:01.000000

"""
from typing import Sequence, Union

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import (  # noqa: E402
    add_column_if_missing,
    column_exists,
    create_index_if_missing,
    drop_index_if_exists,
    index_exists,
)

revision: str = '20260522_layer1_db_refinements'
down_revision: Union[str, None] = '20260522_admin_store'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _replace_check(table: str, name: str, sql: str) -> None:
    # SQLite cannot ALTER CHECK constraints; app-level validation covers Lite dev.
    if op.get_bind().dialect.name == 'sqlite':
        return
    try:
        op.drop_constraint(name, table, type_='check')
    except Exception:
        pass
    op.create_check_constraint(name, table, sa.text(sql))


def upgrade() -> None:
    add_column_if_missing(
        'tenants',
        sa.Column('billing_cycle', sa.String(20), server_default='monthly', nullable=False),
    )
    create_index_if_missing('idx_tenant_plan', 'tenants', ['plan'])

    create_index_if_missing('idx_user_email_verified', 'users', ['email_verified'])
    _replace_check(
        'users',
        'valid_user_role',
        "role IN ('owner', 'admin', 'manager', 'analyst', 'member', 'viewer')",
    )

    _replace_check(
        'memberships',
        'valid_membership_role',
        "role IN ('owner', 'admin', 'manager', 'analyst', 'member', 'viewer')",
    )

    create_index_if_missing('idx_bid_tenant_tender', 'bids', ['tenant_id', 'tender_id'])
    create_index_if_missing('idx_bid_tenant_status', 'bids', ['tenant_id', 'status'])

    create_index_if_missing('idx_proposal_bidder', 'proposals', ['bidder_id'])
    create_index_if_missing('idx_proposal_tenant', 'proposals', ['tenant_id'])
    create_index_if_missing('idx_proposal_tenant_tender', 'proposals', ['tenant_id', 'tender_id'])

    create_index_if_missing('idx_sub_tenant_plan', 'subscriptions', ['tenant_id', 'plan'])
    create_index_if_missing('idx_sub_tenant_status', 'subscriptions', ['tenant_id', 'status'])

    create_index_if_missing('idx_notification_user_created', 'notifications', ['user_id', 'created_at'])
    create_index_if_missing(
        'idx_notification_tenant_created', 'notifications', ['tenant_id', 'created_at']
    )

    create_index_if_missing('idx_usage_resource', 'usage_logs', ['resource_type', 'resource_id'])
    create_index_if_missing('idx_job_tenant_status', 'queue_jobs', ['tenant_id', 'status'])
    create_index_if_missing('idx_ai_provider_type', 'ai_providers', ['provider_type'])


def downgrade() -> None:
    drop_index_if_exists('idx_ai_provider_type', 'ai_providers')
    drop_index_if_exists('idx_job_tenant_status', 'queue_jobs')
    drop_index_if_exists('idx_usage_resource', 'usage_logs')
    drop_index_if_exists('idx_notification_tenant_created', 'notifications')
    drop_index_if_exists('idx_notification_user_created', 'notifications')
    drop_index_if_exists('idx_sub_tenant_status', 'subscriptions')
    drop_index_if_exists('idx_sub_tenant_plan', 'subscriptions')
    drop_index_if_exists('idx_proposal_tenant_tender', 'proposals')
    drop_index_if_exists('idx_proposal_tenant', 'proposals')
    drop_index_if_exists('idx_proposal_bidder', 'proposals')
    drop_index_if_exists('idx_bid_tenant_status', 'bids')
    drop_index_if_exists('idx_bid_tenant_tender', 'bids')

    _replace_check(
        'memberships',
        'valid_membership_role',
        "role IN ('owner', 'admin', 'member', 'viewer')",
    )

    _replace_check(
        'users',
        'valid_user_role',
        "role IN ('owner', 'admin', 'member', 'viewer')",
    )
    drop_index_if_exists('idx_user_email_verified', 'users')

    drop_index_if_exists('idx_tenant_plan', 'tenants')
    if column_exists('tenants', 'billing_cycle'):
        op.drop_column('tenants', 'billing_cycle')
