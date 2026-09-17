from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine


def save_results(run_result: dict, run_id: int, engine: Engine) -> None:
    results = run_result["results"].copy()
    results["run_id"] = run_id
    with engine.begin() as conn:
        if len(results):
            results.to_sql("abc_xyz_results", conn, if_exists="append", index=False)
        conn.execute(
            text(
                """
                UPDATE ingestion_runs
                SET finished_at = :finished_at,
                    status = 'success',
                    rows_ingested_consumption = :rows_consumption,
                    rows_ingested_procurement = :rows_procurement,
                    rows_computed = :rows_computed
                WHERE id = :run_id
                """
            ),
            {
                "finished_at": datetime.now(timezone.utc),
                "rows_consumption": run_result["rows_ingested_consumption"],
                "rows_procurement": run_result["rows_ingested_procurement"],
                "rows_computed": run_result["row_count"],
                "run_id": run_id,
            },
        )


def mark_run_failed(run_id: int, error_message: str, engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE ingestion_runs
                SET finished_at = :finished_at, status = 'error', error_message = :error_message
                WHERE id = :run_id
                """
            ),
            {"finished_at": datetime.now(timezone.utc), "error_message": error_message[:4000], "run_id": run_id},
        )
