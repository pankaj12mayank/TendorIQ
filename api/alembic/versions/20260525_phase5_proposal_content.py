"""Phase 5: proposal title + sections JSON for Lite MVP."""

from alembic import op
import sqlalchemy as sa

revision = '20260525_phase5_proposal'
down_revision = '20260525_phase2_supabase'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('proposals', sa.Column('title', sa.String(500), nullable=True))
    op.add_column('proposals', sa.Column('sections_json', sa.JSON(), nullable=True))
    op.add_column('proposals', sa.Column('model_used', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('proposals', 'model_used')
    op.drop_column('proposals', 'sections_json')
    op.drop_column('proposals', 'title')
