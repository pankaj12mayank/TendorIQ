"""Phase 10: drop leftover enterprise tables (Postgres/MySQL only).

Note: `tenants` is intentionally KEPT — Lite uses it as the personal workspace
(one row per user via personal_workspace bootstrap). Do not drop tenants here.
"""

from alembic import op

revision = '20260525_phase10_cleanup'
down_revision = '20260525_phase8_platform'
branch_labels = None
depends_on = None

# Orphan tables from pre-Lite installs (IF EXISTS only).
_PHASE10_DROP = (
    'site_content',
    'platform_config',
    'feature_flags',
    'api_keys',
    'webhook_deliveries',
    'webhooks',
    'integrations',
    'invitations',
    'team_members',
    'teams',
    'organization_settings',
    'export_jobs',
    'report_templates',
    'saved_searches',
    'tender_tags',
    'tags',
    'comments',
    'attachments',
    'workflows',
    'workflow_runs',
    'agent_sessions',
    'agent_messages',
    'knowledge_bases',
    'knowledge_documents',
    'vector_stores',
    'user_sessions',
    'refresh_tokens',
    'password_reset_tokens',
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        return
    for table in _PHASE10_DROP:
        op.execute(f'DROP TABLE IF EXISTS {table}')


def downgrade() -> None:
    pass
