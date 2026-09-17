from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class WindowResponse(BaseModel):
    window_start: date | None
    window_end: date | None
    computed_at: datetime | None


class KPIResponse(BaseModel):
    total_items: int
    total_consumption_value: float
    a_item_count: int
    x_item_count: int


class ABCXYZMatrixCell(BaseModel):
    abc: str
    xyz: str
    count: int
    value: float


class ABCXYZMatrixResponse(BaseModel):
    cells: list[ABCXYZMatrixCell]
    period_label: str


class ABCXYZMaterialItem(BaseModel):
    item_code: str
    item_description: str | None
    total_consumption_value: float
    cumulative_percent: float
    avg_cv: float | None
    months_count: int
    criticality_score: int | None
    item_category: str | None


class SnapshotOption(BaseModel):
    run_id: int
    window_start: date
    window_end: date
    computed_at: datetime
    label: str


class ItemHistoryPoint(BaseModel):
    run_id: int
    window_start: date
    window_end: date
    computed_at: datetime
    abc_class: str
    xyz_class: str
    total_consumption_value: float


class FinancialYearOption(BaseModel):
    fy_start_year: int
    label: str


class ABCTrendDataPoint(BaseModel):
    month_date: str
    abc_category: str
    value: float


class ABCTrendResponse(BaseModel):
    data: list[ABCTrendDataPoint]
    metric: str
    fy_label: str


class CategoryCountItem(BaseModel):
    category: str
    count: int


class CategoryValueItem(BaseModel):
    category: str
    value: float


class IngestionStatusResponse(BaseModel):
    id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    rows_ingested_consumption: int | None
    rows_ingested_procurement: int | None
    rows_computed: int | None
    error_message: str | None
    consumption_file: str | None
    procurement_file: str | None


class RecomputeRequest(BaseModel):
    consumption_path: str | None = None
    procurement_path: str | None = None


class RecomputeStartedResponse(BaseModel):
    status: str
    run_id: int
    started_at: datetime
