"""append-only abc_xyz_results with run_id

Revision ID: 25bf5de0a89a
Revises: 3a043749769c
Create Date: 2026-09-16 22:05:45.683600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25bf5de0a89a'
down_revision: Union[str, Sequence[str], None] = '3a043749769c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recreate abc_xyz_results as an append-only table keyed by (run_id, item_code).

    Existing rows are recomputed data (no user-authored content), so the table is
    dropped and recreated rather than migrated in place.
    """
    op.drop_table('abc_xyz_results')
    op.create_table(
        'abc_xyz_results',
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('item_description', sa.Text(), nullable=True),
        sa.Column('abc_class', sa.String(length=1), nullable=False),
        sa.Column('total_consumption_value', sa.Numeric(precision=16, scale=2), nullable=False),
        sa.Column('cumulative_percent', sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column('xyz_class', sa.String(length=1), nullable=False),
        sa.Column('avg_cv', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('months_count', sa.Integer(), nullable=False),
        sa.Column('criticality_score', sa.SmallInteger(), nullable=True),
        sa.Column('item_category', sa.String(length=100), nullable=True),
        sa.Column('window_start', sa.Date(), nullable=False),
        sa.Column('window_end', sa.Date(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("abc_class IN ('A','B','C')", name='ck_abc_xyz_results_abc_class'),
        sa.CheckConstraint("xyz_class IN ('X','Y','Z')", name='ck_abc_xyz_results_xyz_class'),
        sa.CheckConstraint('criticality_score IS NULL OR criticality_score BETWEEN 1 AND 5', name='ck_abc_xyz_results_criticality_range'),
        sa.CheckConstraint('months_count >= 0', name='ck_abc_xyz_results_months_nonneg'),
        sa.CheckConstraint('total_consumption_value >= 0', name='ck_abc_xyz_results_value_nonneg'),
        sa.ForeignKeyConstraint(['run_id'], ['ingestion_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('run_id', 'item_code', name='pk_abc_xyz_results'),
    )
    op.create_index(op.f('ix_abc_xyz_results_item_code'), 'abc_xyz_results', ['item_code'], unique=False)
    op.create_index(op.f('ix_abc_xyz_results_run_id'), 'abc_xyz_results', ['run_id'], unique=False)


def downgrade() -> None:
    """Revert to the single-snapshot (latest-only) schema."""
    op.drop_table('abc_xyz_results')
    op.create_table(
        'abc_xyz_results',
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('item_description', sa.Text(), nullable=True),
        sa.Column('abc_class', sa.String(length=1), nullable=False),
        sa.Column('total_consumption_value', sa.Numeric(precision=16, scale=2), nullable=False),
        sa.Column('cumulative_percent', sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column('xyz_class', sa.String(length=1), nullable=False),
        sa.Column('avg_cv', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('months_count', sa.Integer(), nullable=False),
        sa.Column('criticality_score', sa.SmallInteger(), nullable=True),
        sa.Column('item_category', sa.String(length=100), nullable=True),
        sa.Column('window_start', sa.Date(), nullable=False),
        sa.Column('window_end', sa.Date(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("abc_class IN ('A','B','C')", name='ck_abc_xyz_results_abc_class'),
        sa.CheckConstraint("xyz_class IN ('X','Y','Z')", name='ck_abc_xyz_results_xyz_class'),
        sa.CheckConstraint('criticality_score IS NULL OR criticality_score BETWEEN 1 AND 5', name='ck_abc_xyz_results_criticality_range'),
        sa.CheckConstraint('months_count >= 0', name='ck_abc_xyz_results_months_nonneg'),
        sa.CheckConstraint('total_consumption_value >= 0', name='ck_abc_xyz_results_value_nonneg'),
        sa.PrimaryKeyConstraint('item_code'),
    )
