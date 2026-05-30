"""Add queued/extracting/validating processing states, add tender_dashboard analysis type.

Revision ID: 20260530_ai_processing_states
Revises: 20260529_revoked_tokens
"""

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import table_exists  # noqa: E402

revision = '20260530_ai_processing_states'
down_revision = '20260529_revoked_tokens'
branch_labels = None
depends_on = None

NEW_PROCESSING_STATUSES = (
    "'uploaded', 'queued', 'extracting', 'processing', 'validating', "
    "'completed', 'failed', 'retrying', 'needs_review', 'deleted'"
)

NEW_ANALYSIS_TYPES = (
    "'tender_summary', 'bid_review', 'risk_assessment', 'compliance', "
    "'scoring', 'tender_dashboard'"
)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'sqlite':
        with op.batch_alter_table('documents') as batch_op:
            batch_op.drop_constraint('valid_processing_status', type_='check')
            batch_op.create_check_constraint(
                f'processing_status IN ({NEW_PROCESSING_STATUSES})',
                'valid_processing_status',
            )
        with op.batch_alter_table('analysis_results') as batch_op:
            batch_op.drop_constraint('valid_analysis_type', type_='check')
            batch_op.create_check_constraint(
                f'analysis_type IN ({NEW_ANALYSIS_TYPES})',
                'valid_analysis_type',
            )
    elif dialect == 'mysql':
        if table_exists('documents'):
            op.execute(
                f'ALTER TABLE documents DROP CHECK valid_processing_status'
            )
            op.execute(
                f'ALTER TABLE documents ADD CONSTRAINT valid_processing_status '
                f'CHECK (processing_status IN ({NEW_PROCESSING_STATUSES}))'
            )
        if table_exists('analysis_results'):
            op.execute(
                f'ALTER TABLE analysis_results DROP CHECK valid_analysis_type'
            )
            op.execute(
                f'ALTER TABLE analysis_results ADD CONSTRAINT valid_analysis_type '
                f'CHECK (analysis_type IN ({NEW_ANALYSIS_TYPES}))'
            )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    OLD_PROCESSING_STATUSES = (
        "'uploaded', 'processing', 'retrying', 'completed', 'failed', "
        "'needs_review', 'deleted'"
    )
    OLD_ANALYSIS_TYPES = (
        "'tender_summary', 'bid_review', 'risk_assessment', 'compliance', "
        "'scoring'"
    )

    if dialect == 'sqlite':
        with op.batch_alter_table('documents') as batch_op:
            batch_op.drop_constraint('valid_processing_status', type_='check')
            batch_op.create_check_constraint(
                f'processing_status IN ({OLD_PROCESSING_STATUSES})',
                'valid_processing_status',
            )
        with op.batch_alter_table('analysis_results') as batch_op:
            batch_op.drop_constraint('valid_analysis_type', type_='check')
            batch_op.create_check_constraint(
                f'analysis_type IN ({OLD_ANALYSIS_TYPES})',
                'valid_analysis_type',
            )
    elif dialect == 'mysql':
        if table_exists('documents'):
            op.execute(
                f'ALTER TABLE documents DROP CHECK valid_processing_status'
            )
            op.execute(
                f'ALTER TABLE documents ADD CONSTRAINT valid_processing_status '
                f'CHECK (processing_status IN ({OLD_PROCESSING_STATUSES}))'
            )
        if table_exists('analysis_results'):
            op.execute(
                f'ALTER TABLE analysis_results DROP CHECK valid_analysis_type'
            )
            op.execute(
                f'ALTER TABLE analysis_results ADD CONSTRAINT valid_analysis_type '
                f'CHECK (analysis_type IN ({OLD_ANALYSIS_TYPES}))'
            )
