"""Raw-material ABC/XYZ classification pipeline.

Mirrors the value/variability classification logic used for sales data in
Spoorthi_Automation/rolling_abc.py (rolling 12-month window, 70/90 Pareto
cutoffs for ABC, month-over-month coefficient-of-variation for XYZ), applied
here to raw-material consumption instead of sales revenue/quantity.

Two-phase design:
  1. ingest_raw_data(): parses the source Excel files and reloads the
     `raw_consumption` / `raw_procurement` staging tables (full replace).
  2. compute_abc / compute_xyz / enrich: read FROM those staging tables
     (not from Excel again) to produce the final classification.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

CONSUMPTION_SHEET = "RM - Consumption data"

_PROCUREMENT_COLUMN_MAP = {
    "day": "day",
    "month": "month",
    "year": "year",
    "materialid": "material_id",
    "description": "description",
    "procurementquantity": "procurement_qty",
    "unitprice": "unit_price",
    "procurementcost": "procurement_cost",
    "leadtime(days)": "lead_time_days",
    "suppliercode": "supplier_code",
    "suppliername": "supplier_name",
    "pono": "po_no",
    "podate": "po_date",
    "invoicedate": "invoice_date",
    "grnnum": "grn_num",
    "grndate": "grn_date",
    "criticalityscore": "criticality_score",
    "itemcategory": "item_category",
}


def _normalize_key(col: object) -> str:
    return re.sub(r"\s+", "", str(col)).lower()


# ---------------------------------------------------------------------------
# Phase 1: Excel loading
# ---------------------------------------------------------------------------


def load_consumption_excel(path: str) -> pd.DataFrame:
    """Read the 'RM - Consumption data' sheet into a raw_consumption-shaped frame."""
    df = pd.read_excel(path, sheet_name=CONSUMPTION_SHEET, header=1)
    df = df.rename(
        columns={
            "Sl No": "sl_no",
            "Issue Date": "issue_date",
            "Item Code": "item_code",
            "Item Description": "item_description",
            "Consumed Qty": "consumed_qty",
            "Unit Price": "unit_price",
            "Consumption_Cost": "consumption_cost",
        }
    )
    df["issue_date"] = pd.to_datetime(df["issue_date"]).dt.date
    df["item_code"] = df["item_code"].astype(str).str.strip()
    return df[
        ["sl_no", "issue_date", "item_code", "item_description", "consumed_qty", "unit_price", "consumption_cost"]
    ]


def _load_procurement_sheet(path: str, sheet_name: str, source_sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name, header=1)
    rename_map = {}
    for col in df.columns:
        canonical = _PROCUREMENT_COLUMN_MAP.get(_normalize_key(col))
        if canonical:
            rename_map[col] = canonical
    df = df.rename(columns=rename_map)
    df["material_id"] = df["material_id"].astype(str).str.strip()
    df["receipt_date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=df["day"]), errors="coerce"
    ).dt.date
    for date_col in ("po_date", "invoice_date", "grn_date"):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.date
    df["source_sheet"] = source_sheet
    keep_cols = [
        "material_id",
        "description",
        "receipt_date",
        "procurement_qty",
        "unit_price",
        "procurement_cost",
        "lead_time_days",
        "supplier_code",
        "supplier_name",
        "po_no",
        "po_date",
        "invoice_date",
        "grn_num",
        "grn_date",
        "criticality_score",
        "item_category",
        "source_sheet",
    ]
    return df[keep_cols]


def load_procurement_excel(path: str) -> pd.DataFrame:
    """Read + concat both procurement sheets into a raw_procurement-shaped frame."""
    xls = pd.ExcelFile(path)
    real_sheets = [s for s in xls.sheet_names if "RM" in s.upper() and "DATA" in s.upper()]
    if len(real_sheets) != 2:
        raise ValueError(f"Expected exactly 2 procurement data sheets, found {real_sheets} in {path}")

    frames = [_load_procurement_sheet(path, sheet, source_sheet=sheet) for sheet in real_sheets]
    combined = pd.concat(frames, ignore_index=True)

    # Tag sheets "old"/"new" by which has the earlier minimum receipt_date, rather than
    # trusting sheet-name text (names are free-form and have changed before).
    min_dates = combined.groupby("source_sheet")["receipt_date"].min()
    old_sheet_name = min_dates.idxmin()
    combined["source_sheet"] = combined["source_sheet"].apply(
        lambda s: "old" if s == old_sheet_name else "new"
    )
    return combined


# ---------------------------------------------------------------------------
# Phase 1: persist raw data (full replace)
# ---------------------------------------------------------------------------


def ingest_raw_data(consumption_path: str, procurement_path: str, engine: Engine) -> dict:
    consumption_df = load_consumption_excel(consumption_path)
    procurement_df = load_procurement_excel(procurement_path)

    consumption_df = consumption_df.copy()
    consumption_df["source_file"] = str(consumption_path)
    procurement_df = procurement_df.copy()
    procurement_df["source_file"] = str(procurement_path)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE raw_consumption RESTART IDENTITY"))
        conn.execute(text("TRUNCATE TABLE raw_procurement RESTART IDENTITY"))
        consumption_df.to_sql("raw_consumption", conn, if_exists="append", index=False)
        procurement_df.to_sql("raw_procurement", conn, if_exists="append", index=False)

    return {
        "rows_consumption": len(consumption_df),
        "rows_procurement": len(procurement_df),
    }


# ---------------------------------------------------------------------------
# Phase 2: classification, reading from the raw_* staging tables
# ---------------------------------------------------------------------------


def compute_window(max_issue_date: date) -> tuple[date, date]:
    """Rolling 12-month window ending just before the month after the latest data."""
    target_month = (pd.Timestamp(max_issue_date) + pd.offsets.MonthBegin(1)).normalize()
    start_month = target_month - pd.DateOffset(months=12)
    return start_month.date(), target_month.date()


def _load_window_consumption(engine: Engine, window_start: date, window_end: date) -> pd.DataFrame:
    query = text(
        """
        SELECT item_code, item_description, issue_date, consumed_qty, consumption_cost
        FROM raw_consumption
        WHERE issue_date >= :window_start AND issue_date < :window_end
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn, params={"window_start": window_start, "window_end": window_end})
    df["issue_date"] = pd.to_datetime(df["issue_date"])
    df["year_month"] = df["issue_date"].dt.strftime("%Y-%m")
    df["consumed_qty"] = df["consumed_qty"].astype(float)
    df["consumption_cost"] = df["consumption_cost"].astype(float)
    return df


def compute_abc(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["item_code", "item_description"], as_index=False, dropna=False)
        .agg(total_consumption_value=("consumption_cost", "sum"))
    )
    # An item_code can carry multiple descriptions across rows; keep the most frequent one.
    grouped = grouped.sort_values("total_consumption_value", ascending=False)
    grouped = grouped.drop_duplicates(subset="item_code", keep="first").reset_index(drop=True)

    grouped = grouped.sort_values("total_consumption_value", ascending=False).reset_index(drop=True)
    total = grouped["total_consumption_value"].sum()
    grouped["cumulative_value"] = grouped["total_consumption_value"].cumsum()
    grouped["cumulative_percent"] = 100 * grouped["cumulative_value"] / total if total else 0.0

    def classify_abc(pct: float) -> str:
        if pct <= 70:
            return "A"
        if pct <= 90:
            return "B"
        return "C"

    grouped["abc_class"] = grouped["cumulative_percent"].apply(classify_abc)
    return grouped[
        ["item_code", "item_description", "total_consumption_value", "cumulative_percent", "abc_class"]
    ]


def compute_xyz(df: pd.DataFrame) -> pd.DataFrame:
    monthly_qty = (
        df.groupby(["item_code", "year_month"], as_index=False)["consumed_qty"]
        .sum()
        .sort_values(["item_code", "year_month"])
    )
    monthly_qty["prev_qty"] = monthly_qty.groupby("item_code")["consumed_qty"].shift(1)
    monthly_qty["cv"] = (
        (monthly_qty["consumed_qty"] - monthly_qty["prev_qty"]).abs() / monthly_qty["prev_qty"]
    ) * 100
    monthly_qty["cv"] = monthly_qty["cv"].replace([float("inf"), float("-inf")], pd.NA)

    xyz_summary = monthly_qty.groupby("item_code").agg(
        avg_cv=("cv", "mean"),
        months_count=("year_month", "count"),
    ).reset_index()

    def classify_xyz(row) -> str:
        if pd.isna(row["avg_cv"]) or row["months_count"] < 7:
            return "Z"
        if row["avg_cv"] <= 10:
            return "X"
        if row["avg_cv"] <= 25:
            return "Y"
        return "Z"

    xyz_summary["xyz_class"] = xyz_summary.apply(classify_xyz, axis=1)
    return xyz_summary[["item_code", "avg_cv", "months_count", "xyz_class"]]


def merge_abc_xyz(abc_df: pd.DataFrame, xyz_df: pd.DataFrame) -> pd.DataFrame:
    merged = abc_df.merge(xyz_df, on="item_code", how="left")
    merged["xyz_class"] = merged["xyz_class"].fillna("Z")
    merged["months_count"] = merged["months_count"].fillna(0).astype(int)
    return merged


def enrich(abcxyz_df: pd.DataFrame, engine: Engine) -> pd.DataFrame:
    """Left-join the most recent Criticality Score / Item Category per Material ID."""
    query = text(
        """
        SELECT DISTINCT ON (material_id)
            material_id, criticality_score, item_category
        FROM raw_procurement
        ORDER BY material_id, grn_date DESC NULLS LAST, po_date DESC NULLS LAST
        """
    )
    with engine.connect() as conn:
        enrichment_df = pd.read_sql_query(query, conn)
    merged = abcxyz_df.merge(
        enrichment_df, left_on="item_code", right_on="material_id", how="left"
    ).drop(columns=["material_id"])
    return merged


def run_full_pipeline(consumption_path: str, procurement_path: str, engine: Engine) -> dict:
    ingest_counts = ingest_raw_data(consumption_path, procurement_path, engine)

    with engine.connect() as conn:
        max_date_row = conn.execute(text("SELECT MAX(issue_date) FROM raw_consumption")).first()
    if max_date_row is None or max_date_row[0] is None:
        raise ValueError("raw_consumption is empty after ingestion; cannot compute a classification window")
    window_start, window_end = compute_window(max_date_row[0])

    window_df = _load_window_consumption(engine, window_start, window_end)
    abc_df = compute_abc(window_df)
    xyz_df = compute_xyz(window_df)
    merged = merge_abc_xyz(abc_df, xyz_df)
    enriched = enrich(merged, engine)

    enriched["window_start"] = window_start
    enriched["window_end"] = window_end
    enriched["computed_at"] = datetime.now(timezone.utc)

    return {
        "window_start": window_start,
        "window_end": window_end,
        "results": enriched,
        "row_count": len(enriched),
        "computed_at": enriched["computed_at"].iloc[0] if len(enriched) else datetime.now(timezone.utc),
        "rows_ingested_consumption": ingest_counts["rows_consumption"],
        "rows_ingested_procurement": ingest_counts["rows_procurement"],
    }
