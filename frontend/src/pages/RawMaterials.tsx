import { Fragment, useEffect, useMemo, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Typography,
} from '@mui/material';
import { Close as CloseIcon, Inventory2, Payments, ShowChart, Warning } from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { DataGrid, GridToolbar, type GridColDef } from '@mui/x-data-grid';
import { BarChart } from '@mui/x-charts/BarChart';
import { rawMaterialApi } from '../api/rawMaterialApi';
import type {
  ABCXYZMaterialItem,
  ABCXYZMatrixCell,
  CategoryCountItem,
  CategoryValueItem,
  KPIResponse,
  SnapshotOption,
} from '../api/types';
import { ABC_COLORS, ABC_XYZ_COLORS, XYZ_COLORS, formatCurrencyCr, formatNumber } from '../constants/constants';

const ABC_ROWS = ['A', 'B', 'C'] as const;
const XYZ_COLS = ['X', 'Y', 'Z'] as const;

function snapshotMonthLabel(windowEnd: string): string {
  // window_end is exclusive (the month after the snapshot's last data month)
  const [endYear, endMonth] = windowEnd.split('-').map(Number);
  const lastDataMonth = new Date(endYear, endMonth - 1 - 1, 1);
  return lastDataMonth.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' }).replace(' ', '-');
}

interface MatrixPopupState {
  open: boolean;
  abc: string;
  xyz: string;
  loading: boolean;
  items: ABCXYZMaterialItem[];
}

const columns: GridColDef<ABCXYZMaterialItem>[] = [
  { field: 'item_code', headerName: 'Item Code', width: 160 },
  { field: 'item_description', headerName: 'Description', flex: 1, minWidth: 220 },
  {
    field: 'total_consumption_value',
    headerName: 'Total Consumption Value',
    width: 200,
    valueFormatter: (value: number) => formatNumber(value),
  },
  {
    field: 'cumulative_percent',
    headerName: 'Cumulative %',
    width: 130,
    valueFormatter: (value: number) => `${value.toFixed(1)}%`,
  },
  {
    field: 'avg_cv',
    headerName: 'Avg MoM CV',
    width: 130,
    valueFormatter: (value: number | null) => (value === null ? '—' : `${value.toFixed(1)}%`),
  },
  { field: 'months_count', headerName: 'Months of Data', width: 140 },
  { field: 'criticality_score', headerName: 'Criticality', width: 110 },
  { field: 'item_category', headerName: 'Item Category', width: 160 },
];

export function RawMaterials() {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [periodLabel, setPeriodLabel] = useState('');
  const [cells, setCells] = useState<ABCXYZMatrixCell[]>([]);
  const [kpis, setKpis] = useState<KPIResponse | null>(null);
  const [abcCount, setAbcCount] = useState<CategoryCountItem[]>([]);
  const [abcValue, setAbcValue] = useState<CategoryValueItem[]>([]);
  const [xyzCount, setXyzCount] = useState<CategoryCountItem[]>([]);
  const [xyzValue, setXyzValue] = useState<CategoryValueItem[]>([]);
  const [snapshots, setSnapshots] = useState<SnapshotOption[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | ''>('');
  const [popup, setPopup] = useState<MatrixPopupState>({ open: false, abc: '', xyz: '', loading: false, items: [] });

  useEffect(() => {
    rawMaterialApi
      .getSnapshots()
      .then(setSnapshots)
      .catch(() => setSnapshots([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const runId = selectedRunId === '' ? undefined : selectedRunId;
    Promise.allSettled([
      rawMaterialApi.getMatrix(runId),
      rawMaterialApi.getKPIs(runId),
      rawMaterialApi.getAbcCount(runId),
      rawMaterialApi.getAbcValue(runId),
      rawMaterialApi.getXyzCount(runId),
      rawMaterialApi.getXyzValue(runId),
    ]).then(([matrixRes, kpiRes, countRes, valueRes, xyzCountRes, xyzValueRes]) => {
      if (cancelled) return;
      if (matrixRes.status === 'fulfilled') {
        setCells(matrixRes.value.cells);
        setPeriodLabel(matrixRes.value.period_label);
      }
      if (kpiRes.status === 'fulfilled') setKpis(kpiRes.value);
      if (countRes.status === 'fulfilled') setAbcCount(countRes.value);
      if (valueRes.status === 'fulfilled') setAbcValue(valueRes.value);
      if (xyzCountRes.status === 'fulfilled') setXyzCount(xyzCountRes.value);
      if (xyzValueRes.status === 'fulfilled') setXyzValue(xyzValueRes.value);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  const cellFor = useMemo(() => {
    const map = new Map<string, ABCXYZMatrixCell>();
    cells.forEach((c) => map.set(`${c.abc}${c.xyz}`, c));
    return map;
  }, [cells]);

  const handleCellClick = async (abc: string, xyz: string) => {
    setPopup({ open: true, abc, xyz, loading: true, items: [] });
    try {
      const runId = selectedRunId === '' ? undefined : selectedRunId;
      const items = await rawMaterialApi.getMaterials(abc, xyz, runId);
      setPopup((prev) => ({ ...prev, loading: false, items }));
    } catch {
      setPopup((prev) => ({ ...prev, loading: false, items: [] }));
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  const kpiCards = [
    {
      label: 'Materials Classified',
      value: kpis ? formatNumber(kpis.total_items) : '—',
      icon: <Inventory2 />,
      color: ABC_COLORS.Overall,
    },
    {
      label: 'Total Consumption Value',
      value: kpis ? formatCurrencyCr(kpis.total_consumption_value) : '—',
      icon: <Payments />,
      color: ABC_COLORS.B,
    },
    {
      label: 'A-Class Materials',
      value: kpis ? formatNumber(kpis.a_item_count) : '—',
      icon: <ShowChart />,
      color: ABC_COLORS.A,
    },
    {
      label: 'X-Class (Stable Demand)',
      value: kpis ? formatNumber(kpis.x_item_count) : '—',
      icon: <Warning />,
      color: ABC_COLORS.C,
    },
  ];

  const yAxisConfig = (data: number[]) => {
    const max = Math.max(1, ...data);
    return {
      min: 0,
      max: Math.ceil(max * 1.25),
      tickLabelStyle: { fontSize: 12, fontWeight: 600 },
    };
  };

  const yAxisCrConfig = (data: number[]) => ({
    ...yAxisConfig(data),
    valueFormatter: (value: number) => `${value.toFixed(1)} Cr`,
    width: 64,
  });

  return (
    <Box sx={{ width: '100%', boxSizing: 'border-box' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            Raw Material ABC/XYZ Classification
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {periodLabel}
          </Typography>
        </Box>
        <FormControl sx={{ minWidth: 220 }}>
          <InputLabel>Snapshot</InputLabel>
          <Select
            value={selectedRunId}
            label="Snapshot"
            onChange={(e) => setSelectedRunId(e.target.value as number | '')}
            disabled={snapshots.length === 0}
          >
            <MenuItem value="">Latest</MenuItem>
            {snapshots.map((s) => (
              <MenuItem key={s.run_id} value={s.run_id}>
                {snapshotMonthLabel(s.window_end)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* KPI Cards */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
        {kpiCards.map((kpi) => (
          <Box key={kpi.label} sx={{ flexBasis: { xs: '100%', sm: 'calc(50% - 8px)', md: 'calc(25% - 12px)' }, flexGrow: 0, minWidth: 0 }}>
            <Card elevation={0} sx={{ height: '100%', minHeight: 130 }}>
              <CardContent sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, lineHeight: 1, mb: 0.5 }}>
                      {kpi.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                      {kpi.label}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 1.5,
                      bgcolor: `${kpi.color}15`,
                      color: kpi.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: `2px solid ${kpi.color}30`,
                      flexShrink: 0,
                    }}
                  >
                    {kpi.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        ))}
      </Box>

      {/* Matrices */}
      <Box sx={{ display: 'flex', gap: 2, mb: 1, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 320 }}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, fontSize: '0.95rem' }}>
              Consumption Value Matrix
            </Typography>
            <MatrixGrid cellFor={cellFor} metric="value" onCellClick={handleCellClick} />
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 320 }}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, fontSize: '0.95rem' }}>
              Material Count Matrix
            </Typography>
            <MatrixGrid cellFor={cellFor} metric="count" onCellClick={handleCellClick} />
          </Paper>
        </Box>
      </Box>

      {/* Bar Charts */}
      <Typography variant="h6" sx={{ mb: 1, mt: 2, fontWeight: 600 }}>
        ABC Analysis
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 320 }}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Materials by ABC Category
            </Typography>
            <BarChart
              height={300}
              xAxis={[
                {
                  scaleType: 'band',
                  data: abcCount.map((d) => d.category),
                  tickLabelStyle: { fontSize: 14, fontWeight: 600, fill: theme.palette.text.secondary },
                  colorMap: {
                    type: 'ordinal',
                    colors: [ABC_COLORS.A, ABC_COLORS.B, ABC_COLORS.C],
                    values: ['A', 'B', 'C'],
                  },
                },
              ]}
              yAxis={[yAxisConfig(abcCount.map((d) => d.count))]}
              series={[
                {
                  data: abcCount.map((d) => d.count),
                  label: 'Materials',
                  valueFormatter: (v: number | null) => formatNumber(v ?? 0),
                  barLabel: 'value',
                },
              ]}
              slotProps={{ barLabel: { style: { fill: theme.palette.text.primary, fontWeight: 600 } } }}
            />
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 320 }}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Consumption Value by ABC Category
            </Typography>
            <BarChart
              height={300}
              xAxis={[
                {
                  scaleType: 'band',
                  data: abcValue.map((d) => d.category),
                  tickLabelStyle: { fontSize: 14, fontWeight: 600, fill: theme.palette.text.secondary },
                  colorMap: {
                    type: 'ordinal',
                    colors: [ABC_COLORS.A, ABC_COLORS.B, ABC_COLORS.C],
                    values: ['A', 'B', 'C'],
                  },
                },
              ]}
              yAxis={[yAxisCrConfig(abcValue.map((d) => d.value / 10000000))]}
              series={[
                {
                  data: abcValue.map((d) => Number((d.value / 10000000).toFixed(2))),
                  label: 'Value (₹ Cr)',
                  valueFormatter: (v: number | null) => `₹${(v ?? 0).toFixed(2)} Cr`,
                  barLabel: 'value',
                },
              ]}
              slotProps={{ barLabel: { style: { fill: theme.palette.text.primary, fontWeight: 600 } } }}
            />
          </Paper>
        </Box>
      </Box>

      <Typography variant="h6" sx={{ mb: 1, mt: 2, fontWeight: 600 }}>
        XYZ Analysis
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 320 }}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Materials by XYZ Category
            </Typography>
            <BarChart
              height={300}
              xAxis={[
                {
                  scaleType: 'band',
                  data: xyzCount.map((d) => d.category),
                  tickLabelStyle: { fontSize: 14, fontWeight: 600, fill: theme.palette.text.secondary },
                  colorMap: {
                    type: 'ordinal',
                    colors: [XYZ_COLORS.X, XYZ_COLORS.Y, XYZ_COLORS.Z],
                    values: ['X', 'Y', 'Z'],
                  },
                },
              ]}
              yAxis={[yAxisConfig(xyzCount.map((d) => d.count))]}
              series={[
                {
                  data: xyzCount.map((d) => d.count),
                  label: 'Materials',
                  valueFormatter: (v: number | null) => formatNumber(v ?? 0),
                  barLabel: 'value',
                },
              ]}
              slotProps={{ barLabel: { style: { fill: theme.palette.text.primary, fontWeight: 600 } } }}
            />
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 320 }}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Consumption Value by XYZ Category
            </Typography>
            <BarChart
              height={300}
              xAxis={[
                {
                  scaleType: 'band',
                  data: xyzValue.map((d) => d.category),
                  tickLabelStyle: { fontSize: 14, fontWeight: 600, fill: theme.palette.text.secondary },
                  colorMap: {
                    type: 'ordinal',
                    colors: [XYZ_COLORS.X, XYZ_COLORS.Y, XYZ_COLORS.Z],
                    values: ['X', 'Y', 'Z'],
                  },
                },
              ]}
              yAxis={[yAxisCrConfig(xyzValue.map((d) => d.value / 10000000))]}
              series={[
                {
                  data: xyzValue.map((d) => Number((d.value / 10000000).toFixed(2))),
                  label: 'Value (₹ Cr)',
                  valueFormatter: (v: number | null) => `₹${(v ?? 0).toFixed(2)} Cr`,
                  barLabel: 'value',
                },
              ]}
              slotProps={{ barLabel: { style: { fill: theme.palette.text.primary, fontWeight: 600 } } }}
            />
          </Paper>
        </Box>
      </Box>

      <Dialog open={popup.open} onClose={() => setPopup((p) => ({ ...p, open: false }))} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Materials — {popup.abc}
          {popup.xyz}
          <IconButton onClick={() => setPopup((p) => ({ ...p, open: false }))}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ height: 500 }}>
          {popup.loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={popup.items}
              columns={columns}
              getRowId={(row) => row.item_code}
              slots={{ toolbar: GridToolbar }}
              density="compact"
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

function MatrixGrid({
  cellFor,
  metric,
  onCellClick,
}: {
  cellFor: Map<string, ABCXYZMatrixCell>;
  metric: 'value' | 'count';
  onCellClick: (abc: string, xyz: string) => void;
}) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: '50px repeat(3, 1fr)', gap: 1.5 }}>
      <Box />
      {XYZ_COLS.map((xyz) => (
        <Box key={xyz} sx={{ fontWeight: 600, textAlign: 'center', fontSize: '1rem', p: 0.5 }}>
          {xyz}
        </Box>
      ))}
      {ABC_ROWS.map((abc) => (
        <Fragment key={abc}>
          <Box sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem', p: 0.5 }}>
            {abc}
          </Box>
          {XYZ_COLS.map((xyz) => {
            const cell = cellFor.get(`${abc}${xyz}`);
            const bgColor = ABC_XYZ_COLORS[`${abc}${xyz}`] || '#ccc';
            return (
              <Card
                key={`${abc}${xyz}`}
                elevation={1}
                onClick={() => onCellClick(abc, xyz)}
                sx={{
                  bgcolor: `${bgColor}30`,
                  minHeight: 80,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  p: 1,
                  border: `1px solid ${bgColor}`,
                  cursor: 'pointer',
                  transition: 'transform 150ms, opacity 150ms',
                  '&:hover': { opacity: 0.85, transform: 'scale(1.03)' },
                }}
              >
                {metric === 'value' ? (
                  <>
                    <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '1.05rem' }}>
                      ₹{cell ? (cell.value / 10000000).toFixed(2) : '0.00'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Cr
                    </Typography>
                  </>
                ) : (
                  <>
                    <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '1.05rem' }}>
                      {cell ? cell.count : 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Materials
                    </Typography>
                  </>
                )}
              </Card>
            );
          })}
        </Fragment>
      ))}
    </Box>
  );
}
