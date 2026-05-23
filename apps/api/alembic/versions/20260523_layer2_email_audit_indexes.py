"""Layer 2 — email + audit indexes (idempotent).

Revision ID: 20260523_layer2_email_audit_indexes
Revises: 20260522_layer1_db_refinements
Create Date: 2026-05-23 00:00:00.000000
"""
from typing import Sequence, Union

import sys
from os.path import abspath, dirname

from alembic import op

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import create_index_if_missing  # noqa: E402

revision: str = '20260523_layer2_email_audit_indexes'
down_revision: Union[str, None] = '20260522_layer1_db_refinements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    create_index_if_missing('idx_email_template_status', 'email_templates', ['status'])
    create_index_if_missing('idx_email_queue_status_created', 'email_queue', ['status', 'created_at'])
    create_index_if_missing('idx_email_logs_tenant_created', 'email_logs', ['tenant_id', 'created_at'])
    create_index_if_missing('idx_audit_tenant_created', 'audit_logs', ['tenant_id', 'created_at'])
    create_index_if_missing('idx_audit_action', 'audit_logs', ['action_type'])


def downgrade() -> None:
    from migration_utils import drop_index_if_exists

    drop_index_if_exists('idx_audit_action', 'audit_logs')
    drop_index_if_exists('idx_audit_tenant_created', 'audit_logs')
    drop_index_if_exists('idx_email_logs_tenant_created', 'email_logs')
    drop_index_if_exists('idx_email_queue_status_created', 'email_queue')
    drop_index_if_exists('idx_email_template_status', 'email_templates')
