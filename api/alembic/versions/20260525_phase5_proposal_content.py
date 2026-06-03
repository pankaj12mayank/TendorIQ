"""Phase 5: proposal title + sections JSON for Lite MVP."""

import sys
from os.path import abspath, dirname

from alembic import op
import sqlalchemy as sa

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migration_utils import add_column_if_missing  # noqa: E402

revision = '20260525_phase5_proposal'
down_revision = '20260525_phase2_supabase'
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing('proposals', sa.Column('title', sa.String(500), nullable=True))
    add_column_if_missing('proposals', sa.Column('sections_json', sa.JSON(), nullable=True))
    add_column_if_missing('proposals', sa.Column('model_used', sa.String(100), nullable=True))


def downgrade() -> None:
    from migration_utils import drop_column_if_exists

    drop_column_if_exists('proposals', 'model_used')
    drop_column_if_exists('proposals', 'sections_json')
    drop_column_if_exists('proposals', 'title')
