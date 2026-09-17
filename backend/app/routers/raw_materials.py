from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models_orm import AbcXyzResult, RawConsumption, User
from app.schemas import (
    ABCTrendDataPoint,
    ABCTrendResponse,
    ABCXYZMaterialItem,
    ABCXYZMatrixCell,
    ABCXYZMatrixResponse,
    CategoryCountItem,
    CategoryValueItem,
    FinancialYearOption,
    ItemHistoryPoint,
    KPIResponse,
    SnapshotOption,
    WindowResponse,
)

router = APIRouter(prefix="/raw-materials", tags=["Raw Materials"], dependencies=[Depends(get_current_user)])


def _period_label(window_start, window_end) -> str:
    if window_start is None or window_end is None:
        return "No data"
    last_month_end = window_end.replace(day=1)
    last_month = last_month_end - timedelta(days=1)
    return f"{window_start.strftime('%b %Y')} - {last_month.strftime('%b %Y')}"


def _resolve_run_id(db: Session, run_id: int | None) -> int | None:
    """Returns the requested run_id if valid, else the latest run_id with results."""
    if run_id is not None:
        exists = db.query(AbcXyzResult.run_id).filter(AbcXyzResult.run_id == run_id).first()
        if exists:
            return run_id
    latest = db.query(func.max(AbcXyzResult.run_id)).scalar()
    return latest


@router.get("/snapshots", response_model=list[SnapshotOption])
def get_snapshots(db: Session = Depends(get_db)):
    rows = (
        db.query(
            AbcXyzResult.run_id,
            func.min(AbcXyzResult.window_start),
            func.max(AbcXyzResult.window_end),
            func.max(AbcXyzResult.computed_at),
        )
        .group_by(AbcXyzResult.run_id)
        .order_by(AbcXyzResult.run_id.desc())
        .limit(36)
        .all()
    )
    return [
        SnapshotOption(
            run_id=run_id,
            window_start=window_start,
            window_end=window_end,
            computed_at=computed_at,
            label=_period_label(window_start, window_end),
        )
        for run_id, window_start, window_end, computed_at in rows
    ]


@router.get("/window", response_model=WindowResponse)
def get_window(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return WindowResponse(window_start=None, window_end=None, computed_at=None)
    row = (
        db.query(
            func.min(AbcXyzResult.window_start), func.max(AbcXyzResult.window_end), func.max(AbcXyzResult.computed_at)
        )
        .filter(AbcXyzResult.run_id == resolved)
        .first()
    )
    return WindowResponse(window_start=row[0], window_end=row[1], computed_at=row[2])


@router.get("/kpis", response_model=KPIResponse)
def get_kpis(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return KPIResponse(total_items=0, total_consumption_value=0.0, a_item_count=0, x_item_count=0)
    base = db.query(AbcXyzResult).filter(AbcXyzResult.run_id == resolved)
    total_items = base.count()
    total_value = (
        db.query(func.coalesce(func.sum(AbcXyzResult.total_consumption_value), 0))
        .filter(AbcXyzResult.run_id == resolved)
        .scalar()
        or 0
    )
    a_count = base.filter(AbcXyzResult.abc_class == "A").count()
    x_count = base.filter(AbcXyzResult.xyz_class == "X").count()
    return KPIResponse(
        total_items=total_items,
        total_consumption_value=float(total_value),
        a_item_count=a_count,
        x_item_count=x_count,
    )


@router.get("/abc-xyz-matrix", response_model=ABCXYZMatrixResponse)
def get_abc_xyz_matrix(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return ABCXYZMatrixResponse(cells=[], period_label="No data")
    rows = (
        db.query(
            AbcXyzResult.abc_class,
            AbcXyzResult.xyz_class,
            func.count(AbcXyzResult.item_code),
            func.coalesce(func.sum(AbcXyzResult.total_consumption_value), 0),
        )
        .filter(AbcXyzResult.run_id == resolved)
        .group_by(AbcXyzResult.abc_class, AbcXyzResult.xyz_class)
        .all()
    )
    cells = [
        ABCXYZMatrixCell(abc=abc, xyz=xyz, count=count, value=float(value)) for abc, xyz, count, value in rows
    ]
    window = (
        db.query(func.min(AbcXyzResult.window_start), func.max(AbcXyzResult.window_end))
        .filter(AbcXyzResult.run_id == resolved)
        .first()
    )
    return ABCXYZMatrixResponse(cells=cells, period_label=_period_label(window[0], window[1]))


@router.get("/abc-xyz-materials", response_model=list[ABCXYZMaterialItem])
def get_abc_xyz_materials(
    abc: str = Query(..., pattern="^[ABCabc]$"),
    xyz: str = Query(..., pattern="^[XYZxyz]$"),
    run_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return []
    rows = (
        db.query(AbcXyzResult)
        .filter(
            AbcXyzResult.run_id == resolved,
            AbcXyzResult.abc_class == abc.upper(),
            AbcXyzResult.xyz_class == xyz.upper(),
        )
        .order_by(AbcXyzResult.total_consumption_value.desc())
        .all()
    )
    return [
        ABCXYZMaterialItem(
            item_code=r.item_code,
            item_description=r.item_description,
            total_consumption_value=float(r.total_consumption_value),
            cumulative_percent=float(r.cumulative_percent),
            avg_cv=float(r.avg_cv) if r.avg_cv is not None else None,
            months_count=r.months_count,
            criticality_score=r.criticality_score,
            item_category=r.item_category,
        )
        for r in rows
    ]


@router.get("/abc-count", response_model=list[CategoryCountItem])
def get_abc_count(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return []
    rows = (
        db.query(AbcXyzResult.abc_class, func.count(AbcXyzResult.item_code))
        .filter(AbcXyzResult.run_id == resolved)
        .group_by(AbcXyzResult.abc_class)
        .order_by(AbcXyzResult.abc_class)
        .all()
    )
    return [CategoryCountItem(category=abc, count=count) for abc, count in rows]


@router.get("/abc-value", response_model=list[CategoryValueItem])
def get_abc_value(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return []
    rows = (
        db.query(AbcXyzResult.abc_class, func.coalesce(func.sum(AbcXyzResult.total_consumption_value), 0))
        .filter(AbcXyzResult.run_id == resolved)
        .group_by(AbcXyzResult.abc_class)
        .order_by(AbcXyzResult.abc_class)
        .all()
    )
    return [CategoryValueItem(category=abc, value=float(value)) for abc, value in rows]


@router.get("/xyz-count", response_model=list[CategoryCountItem])
def get_xyz_count(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return []
    rows = (
        db.query(AbcXyzResult.xyz_class, func.count(AbcXyzResult.item_code))
        .filter(AbcXyzResult.run_id == resolved)
        .group_by(AbcXyzResult.xyz_class)
        .order_by(AbcXyzResult.xyz_class)
        .all()
    )
    return [CategoryCountItem(category=xyz, count=count) for xyz, count in rows]


@router.get("/xyz-value", response_model=list[CategoryValueItem])
def get_xyz_value(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    resolved = _resolve_run_id(db, run_id)
    if resolved is None:
        return []
    rows = (
        db.query(AbcXyzResult.xyz_class, func.coalesce(func.sum(AbcXyzResult.total_consumption_value), 0))
        .filter(AbcXyzResult.run_id == resolved)
        .group_by(AbcXyzResult.xyz_class)
        .order_by(AbcXyzResult.xyz_class)
        .all()
    )
    return [CategoryValueItem(category=xyz, value=float(value)) for xyz, value in rows]


def _fy_start_year(d: date) -> int:
    return d.year if d.month >= 4 else d.year - 1


@router.get("/available-financial-years", response_model=list[FinancialYearOption])
def get_available_financial_years(db: Session = Depends(get_db)):
    row = db.query(func.min(RawConsumption.issue_date), func.max(RawConsumption.issue_date)).first()
    min_date, max_date = row
    if min_date is None:
        return []
    start_fy = _fy_start_year(min_date)
    end_fy = _fy_start_year(max_date)
    return [
        FinancialYearOption(fy_start_year=fy, label=f"FY {fy}-{str(fy + 1)[-2:]}")
        for fy in range(end_fy, start_fy - 1, -1)
    ]


@router.get("/abc-trend", response_model=ABCTrendResponse)
def get_abc_trend(
    fy_start_year: int | None = Query(None),
    abc_categories: str = Query("A,B,C"),
    xyz_categories: str = Query("X,Y,Z"),
    metric: str = Query("Revenue", pattern="^(Revenue|Quantity)$"),
    db: Session = Depends(get_db),
):
    """Monthly trend of consumption value/quantity by ABC category, using each
    material's LATEST classification tag applied over its full transaction history
    (mirrors the sales dashboard's spoorthi_abc_xyz_datamart trend logic)."""
    if fy_start_year is None:
        max_date = db.query(func.max(RawConsumption.issue_date)).scalar()
        if max_date is None:
            return ABCTrendResponse(data=[], metric=metric, fy_label="No data")
        current_fy_start = _fy_start_year(max_date)
        fy_end_date = date(current_fy_start + 1, 3, 31)
        fy_start_year = current_fy_start if max_date >= fy_end_date else current_fy_start - 1

    fy_start_date = date(fy_start_year, 4, 1)
    fy_end_date_exclusive = date(fy_start_year + 1, 4, 1)
    fy_label = f"FY {fy_start_year}-{str(fy_start_year + 1)[-2:]}"

    abc_list = [c.strip().upper() for c in abc_categories.split(",") if c.strip()]
    xyz_list = [c.strip().upper() for c in xyz_categories.split(",") if c.strip()]
    metric_col = RawConsumption.consumption_cost if metric == "Revenue" else RawConsumption.consumed_qty

    latest_run_id = db.query(func.max(AbcXyzResult.run_id)).scalar()

    year_month_expr = func.to_char(RawConsumption.issue_date, "YYYY-MM")

    filtered_rows = []
    if latest_run_id is not None:
        filtered_rows = (
            db.query(year_month_expr.label("year_month"), AbcXyzResult.abc_class, func.coalesce(func.sum(metric_col), 0))
            .join(AbcXyzResult, AbcXyzResult.item_code == RawConsumption.item_code)
            .filter(
                AbcXyzResult.run_id == latest_run_id,
                AbcXyzResult.abc_class.in_(abc_list),
                AbcXyzResult.xyz_class.in_(xyz_list),
                RawConsumption.issue_date >= fy_start_date,
                RawConsumption.issue_date < fy_end_date_exclusive,
            )
            .group_by(year_month_expr, AbcXyzResult.abc_class)
            .order_by(year_month_expr)
            .all()
        )

    overall_rows = (
        db.query(year_month_expr.label("year_month"), func.coalesce(func.sum(metric_col), 0))
        .filter(RawConsumption.issue_date >= fy_start_date, RawConsumption.issue_date < fy_end_date_exclusive)
        .group_by(year_month_expr)
        .order_by(year_month_expr)
        .all()
    )

    data_points = [
        ABCTrendDataPoint(month_date=f"{ym}-01", abc_category=abc, value=float(value))
        for ym, abc, value in filtered_rows
    ]
    data_points += [
        ABCTrendDataPoint(month_date=f"{ym}-01", abc_category="Overall", value=float(value))
        for ym, value in overall_rows
    ]

    return ABCTrendResponse(data=data_points, metric=metric, fy_label=fy_label)


@router.get("/item-history", response_model=list[ItemHistoryPoint])
def get_item_history(item_code: str = Query(...), db: Session = Depends(get_db)):
    rows = (
        db.query(AbcXyzResult)
        .filter(AbcXyzResult.item_code == item_code)
        .order_by(AbcXyzResult.run_id.asc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No history found for item_code={item_code}")
    return [
        ItemHistoryPoint(
            run_id=r.run_id,
            window_start=r.window_start,
            window_end=r.window_end,
            computed_at=r.computed_at,
            abc_class=r.abc_class,
            xyz_class=r.xyz_class,
            total_consumption_value=float(r.total_consumption_value),
        )
        for r in rows
    ]
