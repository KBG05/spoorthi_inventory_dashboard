import { apiClient } from './client';
import type {
  ABCTrendResponse,
  ABCXYZMaterialItem,
  ABCXYZMatrixResponse,
  CategoryCountItem,
  CategoryValueItem,
  FinancialYearOption,
  IngestionStatusResponse,
  ItemHistoryPoint,
  KPIResponse,
  RecomputeStartedResponse,
  SnapshotOption,
  WindowResponse,
} from './types';

export const rawMaterialApi = {
  getSnapshots: async (): Promise<SnapshotOption[]> => {
    const { data } = await apiClient.get<SnapshotOption[]>('/raw-materials/snapshots');
    return data;
  },
  getWindow: async (runId?: number): Promise<WindowResponse> => {
    const { data } = await apiClient.get<WindowResponse>('/raw-materials/window', { params: { run_id: runId } });
    return data;
  },
  getKPIs: async (runId?: number): Promise<KPIResponse> => {
    const { data } = await apiClient.get<KPIResponse>('/raw-materials/kpis', { params: { run_id: runId } });
    return data;
  },
  getMatrix: async (runId?: number): Promise<ABCXYZMatrixResponse> => {
    const { data } = await apiClient.get<ABCXYZMatrixResponse>('/raw-materials/abc-xyz-matrix', {
      params: { run_id: runId },
    });
    return data;
  },
  getMaterials: async (abc: string, xyz: string, runId?: number): Promise<ABCXYZMaterialItem[]> => {
    const { data } = await apiClient.get<ABCXYZMaterialItem[]>('/raw-materials/abc-xyz-materials', {
      params: { abc, xyz, run_id: runId },
    });
    return data;
  },
  getAbcCount: async (runId?: number): Promise<CategoryCountItem[]> => {
    const { data } = await apiClient.get<CategoryCountItem[]>('/raw-materials/abc-count', { params: { run_id: runId } });
    return data;
  },
  getAbcValue: async (runId?: number): Promise<CategoryValueItem[]> => {
    const { data } = await apiClient.get<CategoryValueItem[]>('/raw-materials/abc-value', { params: { run_id: runId } });
    return data;
  },
  getXyzCount: async (runId?: number): Promise<CategoryCountItem[]> => {
    const { data } = await apiClient.get<CategoryCountItem[]>('/raw-materials/xyz-count', { params: { run_id: runId } });
    return data;
  },
  getXyzValue: async (runId?: number): Promise<CategoryValueItem[]> => {
    const { data } = await apiClient.get<CategoryValueItem[]>('/raw-materials/xyz-value', { params: { run_id: runId } });
    return data;
  },
  getItemHistory: async (itemCode: string): Promise<ItemHistoryPoint[]> => {
    const { data } = await apiClient.get<ItemHistoryPoint[]>('/raw-materials/item-history', {
      params: { item_code: itemCode },
    });
    return data;
  },
  getAvailableFinancialYears: async (): Promise<FinancialYearOption[]> => {
    const { data } = await apiClient.get<FinancialYearOption[]>('/raw-materials/available-financial-years');
    return data;
  },
  getAbcTrend: async (
    fyStartYear: number | undefined,
    abcCategories: string,
    xyzCategories: string,
    metric: 'Revenue' | 'Quantity',
  ): Promise<ABCTrendResponse> => {
    const { data } = await apiClient.get<ABCTrendResponse>('/raw-materials/abc-trend', {
      params: { fy_start_year: fyStartYear, abc_categories: abcCategories, xyz_categories: xyzCategories, metric },
    });
    return data;
  },
};

export const ingestionApi = {
  getStatus: async (): Promise<IngestionStatusResponse> => {
    const { data } = await apiClient.get<IngestionStatusResponse>('/ingestion/status');
    return data;
  },
  recompute: async (): Promise<RecomputeStartedResponse> => {
    const { data } = await apiClient.post<RecomputeStartedResponse>('/ingestion/recompute', {});
    return data;
  },
};
