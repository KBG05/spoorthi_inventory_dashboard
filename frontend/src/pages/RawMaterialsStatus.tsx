import { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Grid, Typography } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { ingestionApi } from '../api/rawMaterialApi';
import type { IngestionStatusResponse } from '../api/types';

const STATUS_COLOR: Record<string, 'success' | 'error' | 'warning'> = {
  success: 'success',
  error: 'error',
  running: 'warning',
};

export function RawMaterialsStatus() {
  const [status, setStatus] = useState<IngestionStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await ingestionApi.getStatus();
      setStatus(data);
      setNotFound(false);
      if (data.status !== 'running' && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch {
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleRecompute = async () => {
    setTriggering(true);
    try {
      await ingestionApi.recompute();
      await fetchStatus();
      pollRef.current = setInterval(fetchStatus, 3000);
    } finally {
      setTriggering(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Ingestion Status</Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={handleRecompute}
          disabled={triggering || status?.status === 'running'}
        >
          {triggering || status?.status === 'running' ? 'Recomputing…' : 'Recompute now'}
        </Button>
      </Box>

      {notFound && <Alert severity="info">No ingestion runs yet. Click "Recompute now" to run the pipeline.</Alert>}

      {status && (
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
                <Chip label={status.status} color={STATUS_COLOR[status.status] ?? 'default'} size="small" />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Started At
                </Typography>
                <Typography variant="body1">{new Date(status.started_at).toLocaleString()}</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Finished At
                </Typography>
                <Typography variant="body1">
                  {status.finished_at ? new Date(status.finished_at).toLocaleString() : '—'}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Materials Computed
                </Typography>
                <Typography variant="body1">{status.rows_computed ?? '—'}</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Consumption Rows Ingested
                </Typography>
                <Typography variant="body1">{status.rows_ingested_consumption ?? '—'}</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Procurement Rows Ingested
                </Typography>
                <Typography variant="body1">{status.rows_ingested_procurement ?? '—'}</Typography>
              </Grid>
              {status.error_message && (
                <Grid size={12}>
                  <Alert severity="error">{status.error_message}</Alert>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
