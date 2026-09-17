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


class RawProcurement(Base):
    __tablename__ = "raw_procurement"
    __table_args__ = (
        CheckConstraint("procurement_qty IS NULL OR procurement_qty >= 0", name="ck_raw_procurement_qty_nonneg"),
        CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="ck_raw_procurement_price_nonneg"),
        CheckConstraint("procurement_cost IS NULL OR procurement_cost >= 0", name="ck_raw_procurement_cost_nonneg"),
        CheckConstraint(
            "criticality_score IS NULL OR criticality_score BETWEEN 1 AND 5",
            name="ck_raw_procurement_criticality_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    procurement_qty: Mapped[float | None] = mapped_column(Numeric(14, 2))
    unit_price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    procurement_cost: Mapped[float | None] = mapped_column(Numeric(16, 2))
    lead_time_days: Mapped[float | None] = mapped_column(Numeric(8, 2))
    supplier_code: Mapped[str | None] = mapped_column(String(50))
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    po_no: Mapped[str | None] = mapped_column(String(50))
    po_date: Mapped[date | None] = mapped_column(Date)
    invoice_date: Mapped[date | None] = mapped_column(Date)
    grn_num: Mapped[str | None] = mapped_column(String(50))
    grn_date: Mapped[date | None] = mapped_column(Date)
    criticality_score: Mapped[int | None] = mapped_column(SmallInteger)
    item_category: Mapped[str | None] = mapped_column(String(100))
    source_sheet: Mapped[str] = mapped_column(String(20), nullable=False)
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
