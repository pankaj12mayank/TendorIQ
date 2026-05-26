"""Lite: drop unused enterprise tables (optional cleanup).

Revision ID: 20260525_lite_drop
Revises: 20260523_layer2_email_audit_indexes
Create Date: 2026-05-25
"""

from alembic import op

revision = '20260525_lite_drop'
down_revision = '20260523_layer2_email_audit_indexes'
branch_labels = None
depends_on = None

_TABLES = (
    'dismissed_failed_jobs',
    'ai_providers',
    'email_logs',
    'email_queue',
    'email_templates',
    'email_events',
    'email_branding',
    'smtp_configs',
    'firebase_configs',
    'password_reset_tokens',
    'prompt_template_versions',
    'prompt_templates',
    'prompt_analytics',
    'prompt_audit_logs',
    'audit_logs',
    'queue_jobs',
    'notifications',
    'onboarding_states',
    'prompt_versions',
    'risks',
    'checklists',
    'bids',
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        return
    for table in _TABLES:
        op.execute(f'DROP TABLE IF EXISTS {table}')


def downgrade() -> None:
    pass
