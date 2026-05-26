"""Phase 8: platform_settings for admin CMS and pricing."""

from alembic import op
import sqlalchemy as sa

revision = '20260525_phase8_platform'
down_revision = '20260525_phase5_proposal'
branch_labels = None
depends_on = None


def upgrade() -> None:
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
