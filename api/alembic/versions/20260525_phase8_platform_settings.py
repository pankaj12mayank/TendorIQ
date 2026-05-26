"""Phase 8: platform_settings for admin CMS and pricing."""

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import table_exists  # noqa: E402

revision = '20260525_phase8_platform'
down_revision = '20260525_phase5_proposal'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists('platform_settings'):
        return
    op.create_table(
        'platform_settings',
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('value_json', sa.JSON(), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table('platform_settings')
