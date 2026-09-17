"""Backfill one ABC/XYZ snapshot per month, mirroring the sales pipeline's cadence of
running the rolling-12-month classification every month over its full data history.

Unlike the sales pipeline (which creates a new Postgres table per month, e.g.
rolling_abc_xyz_summary_2025_07), this reuses the single append-only abc_xyz_results
table: each simulated monthly run gets its own ingestion_runs row (run_id), and that
run_id tags its slice of abc_xyz_results rows. Requires raw_consumption/raw_procurement
to already be populated (run a normal /ingestion/recompute once first).

Usage: python scripts/backfill_snapshots.py
"""

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.automation.abc_xyz import compute_abc, compute_xyz, enrich, merge_abc_xyz, _load_window_consumption
from app.database import engine
from app.models_orm import IngestionRun


def month_range(start: pd.Timestamp, end: pd.Timestamp):
    """Yields month-start Timestamps from start to end inclusive."""
    cur = start
    while cur <= end:
        yield cur
        cur = cur + pd.DateOffset(months=1)


def main() -> None:
    with engine.connect() as conn:
        min_date, max_date = conn.execute(
            text("SELECT MIN(issue_date), MAX(issue_date) FROM raw_consumption")
        ).first()
        (consumption_file,) = conn.execute(text("SELECT source_file FROM raw_consumption LIMIT 1")).first()
        (procurement_file,) = conn.execute(text("SELECT source_file FROM raw_procurement LIMIT 1")).first()

    if min_date is None:
        raise SystemExit("raw_consumption is empty. Run a normal /ingestion/recompute first.")

    # Simulate a monthly run at the end of each month with data, target = month after it.
    first_target = (pd.Timestamp(min_date) + pd.offsets.MonthBegin(1)).normalize()
    last_target = (pd.Timestamp(max_date) + pd.offsets.MonthBegin(1)).normalize()

    targets = list(month_range(first_target, last_target))
    print(f"Backfilling {len(targets)} monthly snapshots: {targets[0].date()} .. {targets[-1].date()}")

    for target_month in targets:
        window_start = (target_month - pd.DateOffset(months=12)).date()
        window_end = target_month.date()

        window_df = _load_window_consumption(engine, window_start, window_end)
        if window_df.empty:
            print(f"  {window_end}: no data in window, skipping")
            continue

        abc_df = compute_abc(window_df)
        xyz_df = compute_xyz(window_df)
        merged = merge_abc_xyz(abc_df, xyz_df)
        enriched = enrich(merged, engine)
        enriched["window_start"] = window_start
        enriched["window_end"] = window_end
        computed_at = datetime.now(timezone.utc)
        enriched["computed_at"] = computed_at

        with Session(engine) as session:
            run = IngestionRun(
                started_at=computed_at,
                finished_at=computed_at,
                status="success",
                rows_ingested_consumption=len(window_df),
                rows_ingested_procurement=None,
                rows_computed=len(enriched),
                consumption_file=consumption_file,
                procurement_file=procurement_file,
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            run_id = run.id

        enriched["run_id"] = run_id
        with engine.begin() as conn:
            enriched.to_sql("abc_xyz_results", conn, if_exists="append", index=False)

        print(f"  {window_start} -> {window_end}: run_id={run_id}, {len(enriched)} materials")

    print("Backfill complete.")


if __name__ == "__main__":
    main()
