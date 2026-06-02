"""Layer2: add payment_transactions ledger table.

Revision ID: 20260527_layer2_payment_transactions
Revises: 20260527_layer1_password_reset
"""

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import create_index_if_missing, table_exists  # noqa: E402

revision = '20260527_layer2_payment_transactions'
down_revision = '20260527_layer1_password_reset'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists('payment_transactions'):
        return
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('order_id', sa.String(length=128), nullable=True),
        sa.Column('payment_id', sa.String(length=128), nullable=True),
        sa.Column('external_customer_id', sa.String(length=128), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('plan', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='created'),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'payment_id', name='uq_payment_provider_payment_id'),
        sa.UniqueConstraint('provider', 'order_id', name='uq_payment_provider_order_id'),
        sa.CheckConstraint("provider IN ('razorpay', 'stripe')", name='valid_payment_provider'),
        sa.CheckConstraint("status IN ('created', 'paid', 'failed', 'refunded')", name='valid_payment_status'),
    )
    create_index_if_missing('ix_payment_transactions_tenant_id', 'payment_transactions', ['tenant_id'])
    create_index_if_missing('ix_payment_transactions_user_id', 'payment_transactions', ['user_id'])
    create_index_if_missing('ix_payment_transactions_subscription_id', 'payment_transactions', ['subscription_id'])
    create_index_if_missing('ix_payment_transactions_provider', 'payment_transactions', ['provider'])
    create_index_if_missing('ix_payment_transactions_order_id', 'payment_transactions', ['order_id'])
    create_index_if_missing('ix_payment_transactions_payment_id', 'payment_transactions', ['payment_id'])
    create_index_if_missing(
        'ix_payment_transactions_external_customer_id',
        'payment_transactions',
        ['external_customer_id'],
    )
    create_index_if_missing('ix_payment_transactions_plan', 'payment_transactions', ['plan'])
    create_index_if_missing('ix_payment_transactions_status', 'payment_transactions', ['status'])
    create_index_if_missing('ix_payment_transactions_paid_at', 'payment_transactions', ['paid_at'])
    create_index_if_missing(
        'idx_payments_tenant_status_created',
        'payment_transactions',
        ['tenant_id', 'status', 'created_at'],
    )
    create_index_if_missing(
        'idx_payments_tenant_provider_created',
        'payment_transactions',
        ['tenant_id', 'provider', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('idx_payments_tenant_provider_created', table_name='payment_transactions')
    op.drop_index('idx_payments_tenant_status_created', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_paid_at', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_status', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_plan', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_external_customer_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_payment_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_order_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_provider', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_subscription_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_user_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_tenant_id', table_name='payment_transactions')
    op.drop_table('payment_transactions')
