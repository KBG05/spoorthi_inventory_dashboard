"""One-time load of the procurement star schema from Inventory_Procurement_raw_file.xlsx.

The workbook (see its 'Notes' sheet) is already normalised:
  - Fact_Procurement: one row per PO line, Transaction_ID = row order in the source file.
  - PO_Time_ID -> Time_Master (Jan 2017 = 1 ... Dec 2026 = 120), derived from PO Date.
  - Supplier_ID / Material_ID / Category_ID -> their *_Master sheets.
  - Actual_Lead_Time_Days uses the 2/4/8-week = 15/30/60-day rule.
  - Cost is kept exactly as in the source (4 rows where qty x price != cost).

IDs are stored as-is so the database links exactly like the workbook. Loading is a
full replace of all five tables, independent of the monthly consumption recompute.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

# sheet name -> (table name, {workbook column: db column})
_SHEETS: dict[str, tuple[str, dict[str, str]]] = {
    "Time_Master": ("time_master", {"Time_ID": "time_id", "Month": "month", "Year": "year"}),
    "Supplier_Master": (
        "supplier_master",
        {"Supplier_ID": "supplier_id", "Supplier_Code": "supplier_code", "Supplier_Name": "supplier_name"},
    ),
    "Material_Master": (
        "material_master",
        {
            "Material_ID": "material_id",
            "Material_Code": "material_code",
            "Description": "description",
            "Criticality_Score": "criticality_score",
        },
    ),
    "Category_Master": ("category_master", {"Category_ID": "category_id", "Item_Category": "item_category"}),
    "Fact_Procurement": (
        "fact_procurement",
        {
            "Transaction_ID": "transaction_id",
            "PO_Time_ID": "po_time_id",
            "Supplier_ID": "supplier_id",
            "Material_ID": "material_id",
            "Category_ID": "category_id",
            "Quantity": "quantity",
            "Unit_Price": "unit_price",
            "Cost": "cost",
            "Actual_Lead_Time_Days": "actual_lead_time_days",
        },
    ),
}

# fact column -> (master table, master key)
_FOREIGN_KEYS = {
    "po_time_id": ("time_master", "time_id"),
    "supplier_id": ("supplier_master", "supplier_id"),
    "material_id": ("material_master", "material_id"),
    "category_id": ("category_master", "category_id"),
}

_MASTER_UNIQUE_KEYS = {
    "time_master": ["year", "month"],
    "supplier_master": ["supplier_code"],
    "material_master": ["material_code"],
    "category_master": ["item_category"],
}


def load_procurement_workbook(path: str) -> dict[str, pd.DataFrame]:
    """Read the five sheets into frames keyed by table name, with db column names."""
    xls = pd.ExcelFile(path)
    missing = [s for s in _SHEETS if s not in xls.sheet_names]
    if missing:
        raise ValueError(f"Missing sheets {missing} in {path} (found {xls.sheet_names})")

    frames: dict[str, pd.DataFrame] = {}
    for sheet, (table, columns) in _SHEETS.items():
        df = pd.read_excel(xls, sheet_name=sheet)
        absent = [c for c in columns if c not in df.columns]
        if absent:
            raise ValueError(f"Sheet {sheet!r} is missing columns {absent}")
        df = df[list(columns)].rename(columns=columns)
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
        frames[table] = df
    return frames


def validate_procurement(frames: dict[str, pd.DataFrame]) -> None:
    """Fail loudly on anything that would break the links described in the Notes sheet."""
    errors: list[str] = []

    time = frames["time_master"]
    expected_ids = (time["year"] - 2017) * 12 + time["month"]
    if not (expected_ids == time["time_id"]).all():
        errors.append("Time_Master: Time_ID does not follow Jan 2017 = 1 numbering")

    for table, unique_cols in _MASTER_UNIQUE_KEYS.items():
        df = frames[table]
        pk = df.columns[0]
        if df[pk].duplicated().any():
            errors.append(f"{table}: duplicate {pk}")
        if df.duplicated(subset=unique_cols).any():
            errors.append(f"{table}: duplicate {unique_cols}")

    fact = frames["fact_procurement"]
    if fact["transaction_id"].duplicated().any():
        errors.append("fact_procurement: duplicate transaction_id")
    if fact.isna().any().any():
        errors.append(f"fact_procurement: missing values in {fact.columns[fact.isna().any()].tolist()}")
    for col, (table, key) in _FOREIGN_KEYS.items():
        orphans = (~fact[col].isin(frames[table][key])).sum()
        if orphans:
            errors.append(f"fact_procurement.{col}: {orphans} rows with no match in {table}")

    if errors:
        raise ValueError("Procurement workbook failed validation:\n  " + "\n  ".join(errors))


def persist_procurement(frames: dict[str, pd.DataFrame], source_file: str, engine: Engine) -> dict[str, int]:
    """Full replace of the star schema in one transaction (masters first, then fact)."""
    fact = frames["fact_procurement"].copy()
    fact["source_file"] = source_file

    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE TABLE fact_procurement, time_master, supplier_master, material_master, category_master")
        )
        for table in _MASTER_UNIQUE_KEYS:
            frames[table].to_sql(table, conn, if_exists="append", index=False)
        fact.to_sql("fact_procurement", conn, if_exists="append", index=False)

    return {table: len(df) for table, df in frames.items()}


def ingest_procurement(path: str, engine: Engine) -> dict[str, int]:
    frames = load_procurement_workbook(path)
    validate_procurement(frames)
    return persist_procurement(frames, str(path), engine)
