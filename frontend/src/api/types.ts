export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  username: string;
  role: string;
}

export interface WindowResponse {
  window_start: string | null;
  window_end: string | null;
  computed_at: string | null;
}

export interface KPIResponse {
  total_items: number;
  total_consumption_value: number;
  a_item_count: number;
  x_item_count: number;
}

export interface ABCXYZMatrixCell {
  abc: 'A' | 'B' | 'C';
  xyz: 'X' | 'Y' | 'Z';
  count: number;
  value: number;
}

export interface ABCXYZMatrixResponse {
  cells: ABCXYZMatrixCell[];
  period_label: string;
}

export interface ABCXYZMaterialItem {
  item_code: string;
  item_description: string | null;
  total_consumption_value: number;
  cumulative_percent: number;
  avg_cv: number | null;
  months_count: number;
  criticality_score: number | null;
  item_category: string | null;
}

export interface CategoryCountItem {
  category: string;
  count: number;
}

export interface CategoryValueItem {
  category: string;
  value: number;
}

export interface IngestionStatusResponse {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: 'running' | 'success' | 'error';
  rows_ingested_consumption: number | null;
  rows_ingested_procurement: number | null;
  rows_computed: number | null;
  error_message: string | null;
  consumption_file: string | null;
  procurement_file: string | null;
}

export interface RecomputeStartedResponse {
  status: string;
  run_id: number;
  started_at: string;
}

export interface SnapshotOption {
  run_id: number;
  window_start: string;
  window_end: string;
  computed_at: string;
  label: string;
}

export interface ItemHistoryPoint {
  run_id: number;
  window_start: string;
  window_end: string;
  computed_at: string;
  abc_class: 'A' | 'B' | 'C';
  xyz_class: 'X' | 'Y' | 'Z';
  total_consumption_value: number;
}

export interface FinancialYearOption {
  fy_start_year: number;
  label: string;
}

export interface ABCTrendDataPoint {
  month_date: string;
  abc_category: string;
  value: number;
}

export interface ABCTrendResponse {
  data: ABCTrendDataPoint[];
  metric: string;
  fy_label: string;
}
