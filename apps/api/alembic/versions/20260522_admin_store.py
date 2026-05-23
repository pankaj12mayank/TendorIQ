"""Initial MySQL schema + platform admin tables (Alembic entry revision).

Revision ID: 20260522_admin_store
Revises:
Create Date: 2026-05-22 00:00:00.000000

Uses SQLAlchemy metadata ``create_all`` so fresh installs get the full model graph
(tenants, tenders, documents, email, ai_providers, dismissed_failed_jobs, etc.).
Incremental changes belong in later revisions (e.g. layer1 refinements).
"""
from typing import Sequence, Union

import sys
from os.path import abspath, dirname

from alembic import op

sys.path.insert(0, dirname(dirname(abspath(__file__))) + '/src')

from core.models import Base  # noqa: E402

revision: str = '20260522_admin_store'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
