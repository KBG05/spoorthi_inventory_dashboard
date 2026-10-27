"""Raw-material ABC/XYZ classification pipeline.

Mirrors the value/variability classification logic used for sales data in
Spoorthi_Automation/rolling_abc.py (rolling 12-month window, 70/90 Pareto
cutoffs for ABC, month-over-month coefficient-of-variation for XYZ), applied
here to raw-material consumption instead of sales revenue/quantity.

Two-phase design:
  1. ingest_raw_data(): parses the consumption Excel file and reloads the
     `raw_consumption` staging table (full replace).
  2. compute_abc / compute_xyz / enrich: read FROM the database (not from Excel
     again) to produce the final classification. Enrichment reads the procurement
     star schema (material_master / fact_procurement), loaded separately by
     app/automation/procurement.py.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

CONSUMPTION_SHEET = "RM - Consumption data"

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


# ---------------------------------------------------------------------------
# Phase 1: persist raw data (full replace)
# ---------------------------------------------------------------------------


def ingest_raw_data(consumption_path: str, engine: Engine) -> dict:
    """Reloads raw_consumption only. Procurement lives in the star schema, which is
    loaded once by scripts/load_procurement.py and is not touched here."""
    consumption_df = load_consumption_excel(consumption_path)

    consumption_df = consumption_df.copy()
    consumption_df["source_file"] = str(consumption_path)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE raw_consumption RESTART IDENTITY"))
        consumption_df.to_sql("raw_consumption", conn, if_exists="append", index=False)
        rows_procurement = conn.execute(text("SELECT COUNT(*) FROM fact_procurement")).scalar_one()

    return {
        "rows_consumption": len(consumption_df),
        "rows_procurement": rows_procurement,
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
    """Left-join Criticality Score (from material_master) and the Item Category of the
    most recent PO line per material (latest PO month, then latest transaction)."""
    query = text(
        """
        SELECT m.material_code, m.criticality_score, latest.item_category
        FROM material_master m
        LEFT JOIN LATERAL (
            SELECT c.item_category
            FROM fact_procurement f
            JOIN category_master c ON c.category_id = f.category_id
            WHERE f.material_id = m.material_id
            ORDER BY f.po_time_id DESC, f.transaction_id DESC
            LIMIT 1
        ) latest ON TRUE
        """
    )
    with engine.connect() as conn:
        enrichment_df = pd.read_sql_query(query, conn)
    merged = abcxyz_df.merge(
        enrichment_df, left_on="item_code", right_on="material_code", how="left"
    ).drop(columns=["material_code"])
    return merged


def run_full_pipeline(consumption_path: str, engine: Engine) -> dict:
    ingest_counts = ingest_raw_data(consumption_path, engine)

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
