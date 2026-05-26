"""Phase 1: user-scoped owner_id + company_profiles.

Revision ID: 20260525_phase1_user
Revises: 20260525_lite_drop
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa

revision = '20260525_phase1_user'
down_revision = '20260525_lite_drop'
branch_labels = None
depends_on = None


def _uuid_col():
    return sa.Column('id', sa.String(36), primary_key=True)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        return

    op.create_table(
        'company_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('tax_id', sa.String(100), nullable=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.UniqueConstraint('user_id', name='uq_company_profiles_user_id'),
    )
    op.create_index('idx_company_profiles_user', 'company_profiles', ['user_id'])

    for table in ('tenders', 'documents', 'analysis_results', 'proposals'):
        op.add_column(table, sa.Column('owner_id', sa.String(36), nullable=True))
        op.create_foreign_key(
            f'fk_{table}_owner_id_users',
            table,
            'users',
            ['owner_id'],
            ['id'],
            ondelete='CASCADE',
        )
        op.create_index(f'idx_{table}_owner_id', table, ['owner_id'])

    # Backfill tenders from created_by_id
    op.execute(
        'UPDATE tenders SET owner_id = created_by_id WHERE owner_id IS NULL AND created_by_id IS NOT NULL'
    )
    op.execute(
        'UPDATE proposals SET owner_id = bidder_id WHERE owner_id IS NULL AND bidder_id IS NOT NULL'
    )
    # Documents: assign owner from tender creator where linked
    op.execute(
        """
        UPDATE documents d
        INNER JOIN tenders t ON d.tender_id = t.id
        SET d.owner_id = t.owner_id
        WHERE d.owner_id IS NULL AND t.owner_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE analysis_results ar
        INNER JOIN tenders t ON ar.tender_id = t.id
        SET ar.owner_id = t.owner_id
        WHERE ar.owner_id IS NULL AND t.owner_id IS NOT NULL
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        return
    for table in ('proposals', 'analysis_results', 'documents', 'tenders'):
        op.drop_constraint(f'fk_{table}_owner_id_users', table, type_='foreignkey')
        op.drop_index(f'idx_{table}_owner_id', table_name=table)
        op.drop_column(table, 'owner_id')
    op.drop_index('idx_company_profiles_user', table_name='company_profiles')
    op.drop_table('company_profiles')
