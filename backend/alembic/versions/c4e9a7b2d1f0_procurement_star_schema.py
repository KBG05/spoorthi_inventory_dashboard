"""replace raw_procurement with procurement star schema

Revision ID: c4e9a7b2d1f0
Revises: 8f1c2d3e4a5b
Create Date: 2026-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e9a7b2d1f0'
down_revision: Union[str, Sequence[str], None] = '8f1c2d3e4a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('time_master',
    sa.Column('time_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('month', sa.SmallInteger(), nullable=False),
    sa.Column('year', sa.SmallInteger(), nullable=False),
    sa.CheckConstraint('month BETWEEN 1 AND 12', name='ck_time_master_month_range'),
    sa.PrimaryKeyConstraint('time_id'),
    sa.UniqueConstraint('year', 'month', name='uq_time_master_year_month')
    )
    op.create_table('supplier_master',
    sa.Column('supplier_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('supplier_code', sa.String(length=50), nullable=False),
    sa.Column('supplier_name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('supplier_id'),
    sa.UniqueConstraint('supplier_code')
    )
    op.create_table('material_master',
    sa.Column('material_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('material_code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('criticality_score', sa.SmallInteger(), nullable=True),
    sa.CheckConstraint('criticality_score IS NULL OR criticality_score BETWEEN 1 AND 5', name='ck_material_master_criticality_range'),
    sa.PrimaryKeyConstraint('material_id'),
    sa.UniqueConstraint('material_code')
    )
    op.create_table('category_master',
    sa.Column('category_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('item_category', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('category_id'),
    sa.UniqueConstraint('item_category')
    )
    op.create_table('fact_procurement',
    sa.Column('transaction_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('po_time_id', sa.Integer(), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('material_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('cost', sa.Numeric(precision=16, scale=2), nullable=False),
    sa.Column('actual_lead_time_days', sa.Integer(), nullable=False),
    sa.Column('source_file', sa.String(length=255), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('quantity >= 0', name='ck_fact_procurement_qty_nonneg'),
    sa.CheckConstraint('unit_price >= 0', name='ck_fact_procurement_price_nonneg'),
    sa.CheckConstraint('cost >= 0', name='ck_fact_procurement_cost_nonneg'),
    sa.CheckConstraint('actual_lead_time_days >= 0', name='ck_fact_procurement_lead_time_nonneg'),
    sa.ForeignKeyConstraint(['po_time_id'], ['time_master.time_id']),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier_master.supplier_id']),
    sa.ForeignKeyConstraint(['material_id'], ['material_master.material_id']),
    sa.ForeignKeyConstraint(['category_id'], ['category_master.category_id']),
    sa.PrimaryKeyConstraint('transaction_id')
    )
    op.create_index(op.f('ix_fact_procurement_po_time_id'), 'fact_procurement', ['po_time_id'], unique=False)
    op.create_index(op.f('ix_fact_procurement_supplier_id'), 'fact_procurement', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_fact_procurement_material_id'), 'fact_procurement', ['material_id'], unique=False)
    op.create_index(op.f('ix_fact_procurement_category_id'), 'fact_procurement', ['category_id'], unique=False)

    op.drop_index(op.f('ix_raw_procurement_receipt_date'), table_name='raw_procurement')
    op.drop_index(op.f('ix_raw_procurement_material_id'), table_name='raw_procurement')
    op.drop_table('raw_procurement')


def downgrade() -> None:
    op.create_table('raw_procurement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('material_id', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('receipt_date', sa.Date(), nullable=False),
    sa.Column('procurement_qty', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('procurement_cost', sa.Numeric(precision=16, scale=2), nullable=True),
    sa.Column('lead_time_days', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('supplier_code', sa.String(length=50), nullable=True),
    sa.Column('supplier_name', sa.String(length=255), nullable=True),
    sa.Column('po_no', sa.String(length=50), nullable=True),
    sa.Column('po_date', sa.Date(), nullable=True),
    sa.Column('invoice_date', sa.Date(), nullable=True),
    sa.Column('grn_num', sa.String(length=50), nullable=True),
    sa.Column('grn_date', sa.Date(), nullable=True),
    sa.Column('criticality_score', sa.SmallInteger(), nullable=True),
    sa.Column('item_category', sa.String(length=100), nullable=True),
    sa.Column('source_sheet', sa.String(length=20), nullable=False),
    sa.Column('source_file', sa.String(length=255), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('criticality_score IS NULL OR criticality_score BETWEEN 1 AND 5', name='ck_raw_procurement_criticality_range'),
    sa.CheckConstraint('procurement_cost IS NULL OR procurement_cost >= 0', name='ck_raw_procurement_cost_nonneg'),
    sa.CheckConstraint('procurement_qty IS NULL OR procurement_qty >= 0', name='ck_raw_procurement_qty_nonneg'),
    sa.CheckConstraint('unit_price IS NULL OR unit_price >= 0', name='ck_raw_procurement_price_nonneg'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_procurement_material_id'), 'raw_procurement', ['material_id'], unique=False)
    op.create_index(op.f('ix_raw_procurement_receipt_date'), 'raw_procurement', ['receipt_date'], unique=False)

    op.drop_table('fact_procurement')
    op.drop_table('category_master')
    op.drop_table('material_master')
    op.drop_table('supplier_master')
    op.drop_table('time_master')
