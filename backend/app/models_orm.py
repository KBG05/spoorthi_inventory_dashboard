from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RawConsumption(Base):
    __tablename__ = "raw_consumption"
    __table_args__ = (
        CheckConstraint("consumed_qty >= 0", name="ck_raw_consumption_qty_nonneg"),
        CheckConstraint("unit_price >= 0", name="ck_raw_consumption_price_nonneg"),
        CheckConstraint("consumption_cost >= 0", name="ck_raw_consumption_cost_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sl_no: Mapped[int | None]
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    item_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_description: Mapped[str | None] = mapped_column(Text)
    consumed_qty: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    consumption_cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Procurement star schema, loaded once from Inventory_Procurement_raw_file.xlsx
# (scripts/load_procurement.py). IDs are kept exactly as in the workbook so the
# fact table links to the masters the same way the workbook's Notes describe.
# ---------------------------------------------------------------------------


class TimeMaster(Base):
    """One row per calendar month: Jan 2017 = 1 ... Dec 2026 = 120, no gaps."""

    __tablename__ = "time_master"
    __table_args__ = (
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_time_master_month_range"),
        UniqueConstraint("year", "month", name="uq_time_master_year_month"),
    )

    time_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class SupplierMaster(Base):
    __tablename__ = "supplier_master"

    supplier_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    supplier_name: Mapped[str | None] = mapped_column(String(255))


class MaterialMaster(Base):
    """material_code is the same key as raw_consumption.item_code."""

    __tablename__ = "material_master"
    __table_args__ = (
        CheckConstraint(
            "criticality_score IS NULL OR criticality_score BETWEEN 1 AND 5",
            name="ck_material_master_criticality_range",
        ),
    )

    material_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    material_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    criticality_score: Mapped[int | None] = mapped_column(SmallInteger)


class CategoryMaster(Base):
    __tablename__ = "category_master"

    category_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    item_category: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class FactProcurement(Base):
    """One row per PO line. po_time_id is the PO month (derived from PO Date, not GRN
    date). Category lives here, not on the material, because it varies per PO line
    for the same material. Cost is kept as in the source even where qty x price != cost."""

    __tablename__ = "fact_procurement"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_fact_procurement_qty_nonneg"),
        CheckConstraint("unit_price >= 0", name="ck_fact_procurement_price_nonneg"),
        CheckConstraint("cost >= 0", name="ck_fact_procurement_cost_nonneg"),
        CheckConstraint("actual_lead_time_days >= 0", name="ck_fact_procurement_lead_time_nonneg"),
    )

    transaction_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    po_time_id: Mapped[int] = mapped_column(ForeignKey("time_master.time_id"), nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("supplier_master.supplier_id"), nullable=False, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("material_master.material_id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category_master.category_id"), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    actual_lead_time_days: Mapped[int] = mapped_column(nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AbcXyzResult(Base):
    """One classification snapshot row. Rows are appended per ingestion run (never
    replaced), so a material's classification history across runs can be queried
    by item_code. `run_id` identifies which snapshot/run a row belongs to."""

    __tablename__ = "abc_xyz_results"
    __table_args__ = (
        PrimaryKeyConstraint("run_id", "item_code", name="pk_abc_xyz_results"),
        CheckConstraint("abc_class IN ('A','B','C')", name="ck_abc_xyz_results_abc_class"),
        CheckConstraint("xyz_class IN ('X','Y','Z')", name="ck_abc_xyz_results_xyz_class"),
        CheckConstraint("total_consumption_value >= 0", name="ck_abc_xyz_results_value_nonneg"),
        CheckConstraint("months_count >= 0", name="ck_abc_xyz_results_months_nonneg"),
        CheckConstraint(
            "criticality_score IS NULL OR criticality_score BETWEEN 1 AND 5",
            name="ck_abc_xyz_results_criticality_range",
        ),
    )

    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True)
    item_code: Mapped[str] = mapped_column(String(50), index=True)
    item_description: Mapped[str | None] = mapped_column(Text)
    abc_class: Mapped[str] = mapped_column(String(1), nullable=False)
    total_consumption_value: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    cumulative_percent: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    xyz_class: Mapped[str] = mapped_column(String(1), nullable=False)
    avg_cv: Mapped[float | None] = mapped_column(Numeric(10, 4))
    months_count: Mapped[int] = mapped_column(nullable=False)
    criticality_score: Mapped[int | None] = mapped_column(SmallInteger)
    item_category: Mapped[str | None] = mapped_column(String(100))
    window_start: Mapped[date] = mapped_column(Date, nullable=False)
    window_end: Mapped[date] = mapped_column(Date, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint("status IN ('running','success','error')", name="ck_ingestion_runs_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    rows_ingested_consumption: Mapped[int | None]
    rows_ingested_procurement: Mapped[int | None]
    rows_computed: Mapped[int | None]
    error_message: Mapped[str | None] = mapped_column(Text)
    consumption_file: Mapped[str | None] = mapped_column(String(255))
    procurement_file: Mapped[str | None] = mapped_column(String(255))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, server_default="viewer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
