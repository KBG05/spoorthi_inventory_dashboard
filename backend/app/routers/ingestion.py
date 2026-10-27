from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.automation.abc_xyz import run_full_pipeline
from app.automation.persist import mark_run_failed, save_results
from app.config import settings
from app.database import engine, get_db
from app.models_orm import IngestionRun, User
from app.schemas import IngestionStatusResponse, RecomputeRequest, RecomputeStartedResponse

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


def _run_pipeline_background(run_id: int, consumption_path: str) -> None:
    try:
        result = run_full_pipeline(consumption_path, engine)
        save_results(result, run_id, engine)
    except Exception as exc:  # noqa: BLE001 - surfaced via ingestion_runs.error_message
        mark_run_failed(run_id, str(exc), engine)


@router.post("/recompute", response_model=RecomputeStartedResponse)
def trigger_recompute(
    payload: RecomputeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consumption_path = payload.consumption_path or str(settings.consumption_file)

    run = IngestionRun(
        started_at=datetime.now(timezone.utc),
        status="running",
        consumption_file=consumption_path,
        # Procurement is not re-read on recompute; this records which workbook the
        # one-time star-schema load came from.
        procurement_file=str(settings.procurement_file),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(_run_pipeline_background, run.id, consumption_path)

    return RecomputeStartedResponse(status="started", run_id=run.id, started_at=run.started_at)


@router.get("/status", response_model=IngestionStatusResponse)
def get_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    run = db.query(IngestionRun).order_by(IngestionRun.id.desc()).first()
    if run is None:
        raise HTTPException(status_code=404, detail="No ingestion runs yet")
    return run
