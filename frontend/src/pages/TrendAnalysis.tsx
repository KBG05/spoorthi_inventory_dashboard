import { memo, useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Checkbox,
  CircularProgress,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { LineChart } from '@mui/x-charts/LineChart';
import type { AxisValueFormatterContext } from '@mui/x-charts/internals';
import { rawMaterialApi } from '../api/rawMaterialApi';
import type { ABCTrendResponse, FinancialYearOption } from '../api/types';
import { ABC_COLORS } from '../constants/constants';

type Metric = 'Revenue' | 'Quantity';

interface ChartConfig {
  formattedDates: string[];
  chartSeries: {
    type: 'line';
    id: string;
    label: string;
    data: (number | null)[];
    color: string;
    curve: 'linear';
    showMark: boolean;
    valueFormatter: (value: number | null) => string;
  }[];
}

const ABCTrendChart = memo(({ chartConfig, metric }: { chartConfig: ChartConfig; metric: Metric }) => {
  const theme = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const [chartHeight, setChartHeight] = useState(420);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const h = entries[0].contentRect.height;
      if (h > 50) setChartHeight(h);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  if (chartConfig.chartSeries.length === 0) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
        <Typography color="text.secondary">No data available for selected filters</Typography>
      </Box>
    );
  }

  return (
    <Box ref={containerRef} sx={{ width: '100%', flex: 1, minHeight: 0 }}>
      <LineChart
        height={chartHeight}
        xAxis={[
          {
            scaleType: 'point',
            data: chartConfig.formattedDates,
            height: 44,
            tickLabelStyle: { fontSize: 12, fontWeight: 600, fill: theme.palette.text.secondary },
            valueFormatter: (value: string, context: AxisValueFormatterContext) =>
              context.location === 'tick' ? value.split(' ')[0] : value,
          },
        ]}
        yAxis={[
          {
            width: 80,
            valueFormatter: (value: number, context: AxisValueFormatterContext) => {
              if (metric === 'Revenue') {
                const crValue = value / 10000000;
                if (context.location === 'tick') {
                  if (crValue >= 100) return `₹${crValue.toFixed(0)}Cr`;
                  if (crValue >= 1) return `₹${crValue.toFixed(1)}Cr`;
                  return `₹${crValue.toFixed(2)}Cr`;
                }
                return `₹${crValue.toLocaleString('en-IN', { maximumFractionDigits: 2 })} Cr`;
              }
              if (context.location === 'tick') {
                if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
                return value.toFixed(0);
              }
              return value.toLocaleString('en-IN');
            },
            min: 0,
          },
        ]}
        series={chartConfig.chartSeries}
        margin={{ top: 20, bottom: 20, left: 0, right: 30 }}
        grid={{ vertical: false, horizontal: true }}
        slotProps={{ mark: { style: { strokeWidth: 2 } } }}
        sx={{
          width: '100%',
          '& .MuiChartsTooltip-mark': { ry: 4, rx: 4 },
          '& .MuiChartsAxis-tickLabel': { fill: theme.palette.text.secondary },
        }}
      />
    </Box>
  );
});

export function TrendAnalysis() {
  const [loading, setLoading] = useState(true);
  const [trendData, setTrendData] = useState<ABCTrendResponse | null>(null);
  const [financialYear, setFinancialYear] = useState<number | ''>('');
  const [availableYears, setAvailableYears] = useState<FinancialYearOption[]>([]);
  const [abcCategories, setAbcCategories] = useState<string[]>(['A', 'B', 'C']);
  const [xyzCategories, setXyzCategories] = useState<string[]>(['X', 'Y', 'Z']);
  const [metric, setMetric] = useState<Metric>('Revenue');

  const handleAbcChange = (category: string) => {
    setAbcCategories((prev) => (prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]));
  };

  const handleXyzChange = (category: string) => {
    setXyzCategories((prev) => (prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]));
  };

  useEffect(() => {
    rawMaterialApi
      .getAvailableFinancialYears()
      .then((years) => {
        setAvailableYears(years);
        if (years.length > 0) setFinancialYear(years[0].fy_start_year);
        else setLoading(false);
      })
      .catch(() => {
        setAvailableYears([]);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (financialYear === '' || abcCategories.length === 0 || xyzCategories.length === 0) return;
    let cancelled = false;
    setLoading(true);
    rawMaterialApi
      .getAbcTrend(financialYear, abcCategories.join(','), xyzCategories.join(','), metric)
      .then((res) => {
        if (!cancelled) setTrendData(res);
      })
      .catch(() => {
        if (!cancelled) setTrendData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [financialYear, abcCategories, xyzCategories, metric]);

  const chartConfig = useMemo<ChartConfig>(() => {
    if (!trendData || trendData.data.length === 0) return { formattedDates: [], chartSeries: [] };

    const uniqueDates = [...new Set(trendData.data.map((d) => d.month_date))].sort();
    const availableCategories = [...new Set(trendData.data.map((d) => d.abc_category))];

    const formattedDates = uniqueDates.map((d) => {
      const [year, month] = d.split('-').map(Number);
      return new Date(year, month - 1, 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    });

    const chartSeries = availableCategories
      .filter((cat) => ['A', 'B', 'C', 'Overall'].includes(cat))
      .sort((a, b) => {
        if (a === 'Overall') return -1;
        if (b === 'Overall') return 1;
        return a.localeCompare(b);
      })
      .map((cat) => {
        const categoryData = trendData.data.filter((d) => d.abc_category === cat);
        return {
          type: 'line' as const,
          id: `series-${cat}`,
          label: cat,
          data: uniqueDates.map((d) => {
            const point = categoryData.find((p) => p.month_date === d);
            return point?.value ?? null;
          }),
          color:
            cat === 'A' ? ABC_COLORS.A : cat === 'B' ? ABC_COLORS.B : cat === 'C' ? ABC_COLORS.C : ABC_COLORS.Overall,
          curve: 'linear' as const,
          showMark: true,
          valueFormatter: (value: number | null) => {
            if (value === null) return '';
            if (metric === 'Revenue') return `₹${(value / 10000000).toFixed(2)} Cr`;
            return value.toLocaleString('en-IN');
          },
        };
      });

    return { formattedDates, chartSeries };
  }, [trendData, metric]);

  return (
    <Box sx={{ width: '100%', height: '100%', boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" sx={{ mb: 2, fontWeight: 600 }}>
        Trend Analysis
      </Typography>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Paper elevation={1} sx={{ p: 2.5, mb: 2, width: '100%', boxSizing: 'border-box', flexShrink: 0 }}>
            <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'flex-start' }}>
              <FormControl sx={{ minWidth: 180 }}>
                <InputLabel>Financial Year</InputLabel>
                <Select
                  value={financialYear}
                  label="Financial Year"
                  onChange={(e) => setFinancialYear(e.target.value as number)}
                  size="small"
                  disabled={availableYears.length === 0}
                >
                  {availableYears.map((fy) => (
                    <MenuItem key={fy.fy_start_year} value={fy.fy_start_year}>
                      {fy.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box>
                <FormLabel component="legend" sx={{ mb: 1, fontWeight: 500, fontSize: '0.875rem' }}>
                  ABC Categories
                </FormLabel>
                <FormGroup row>
                  {['A', 'B', 'C'].map((cat) => (
                    <FormControlLabel
                      key={cat}
                      control={<Checkbox checked={abcCategories.includes(cat)} onChange={() => handleAbcChange(cat)} size="small" />}
                      label={cat}
                    />
                  ))}
                </FormGroup>
              </Box>

              <Box>
                <FormLabel component="legend" sx={{ mb: 1, fontWeight: 500, fontSize: '0.875rem' }}>
                  XYZ Categories
                </FormLabel>
                <FormGroup row>
                  {['X', 'Y', 'Z'].map((cat) => (
                    <FormControlLabel
                      key={cat}
                      control={<Checkbox checked={xyzCategories.includes(cat)} onChange={() => handleXyzChange(cat)} size="small" />}
                      label={cat}
                    />
                  ))}
                </FormGroup>
              </Box>

              <Box>
                <FormLabel component="legend" sx={{ mb: 1, fontWeight: 500, fontSize: '0.875rem' }}>
                  Metric
                </FormLabel>
                <ToggleButtonGroup
                  value={metric}
                  exclusive
                  onChange={(_, newMetric) => newMetric && setMetric(newMetric)}
                  size="small"
                >
                  <ToggleButton value="Revenue" sx={{ px: 2.5 }}>
                    Revenue
                  </ToggleButton>
                  <ToggleButton value="Quantity" sx={{ px: 2.5 }}>
                    Quantity
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>
            </Box>
          </Paper>

          <Paper
            elevation={1}
            sx={{ p: 2.5, flex: 1, width: '100%', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', minHeight: 0 }}
          >
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, flexShrink: 0 }}>
              {metric} Trend by ABC Category
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2, flexShrink: 0 }}>
              {metric === 'Revenue' ? 'Values in crores (Cr)' : 'Consumed quantity'} • {trendData?.fy_label}
            </Typography>

            {trendData && trendData.data.length > 0 ? (
              <ABCTrendChart chartConfig={chartConfig} metric={metric} />
            ) : (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                <Typography color="text.secondary">No data available for selected filters</Typography>
              </Box>
            )}
          </Paper>
        </>
      )}
    </Box>
  );
}
