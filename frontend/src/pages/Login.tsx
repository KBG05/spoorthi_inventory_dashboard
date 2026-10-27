import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Alert,
  AppBar,
  Box,
  Button,
  CircularProgress,
  Container,
  IconButton,
  Paper,
  TextField,
  Toolbar,
  Typography,
} from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useThemeMode } from '../theme/ThemeProvider';

export function Login() {
  const { user, login } = useAuth();
  const { mode, toggleTheme } = useThemeMode();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/raw-materials" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
    } catch {
      setError('Invalid username or password');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: 40,
              px: 1.5,
              mr: 1.5,
              borderRadius: 1.5,
              bgcolor: mode === 'light' ? 'rgba(64, 91, 130, 0.1)' : 'rgba(255, 255, 255, 0.5)',
              border: '1px solid',
              borderColor: mode === 'light' ? 'rgba(64, 91, 130, 0.25)' : 'rgba(255, 255, 255, 0.3)',
            }}
          >
            <img src={`${import.meta.env.BASE_URL}Spoorthi-Logo.png`} alt="Spoorthi Logo" style={{ height: 30, width: 'auto', display: 'block' }} />
          </Box>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Raw Material Inventory
          </Typography>
          <IconButton onClick={toggleTheme} color="inherit">
            {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="sm">
        <Box
          sx={{
            minHeight: 'calc(100vh - 64px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            py: 4,
          }}
        >
          <Paper elevation={3} sx={{ p: 4, width: '100%', maxWidth: 400 }}>
            <Typography variant="h4" align="center" sx={{ mb: 3 }}>
              Login
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Username"
                type="text"
                variant="outlined"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                sx={{ mb: 2 }}
                disabled={submitting}
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                variant="outlined"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                sx={{ mb: 3 }}
                disabled={submitting}
              />
              <Button fullWidth type="submit" variant="contained" size="large" disabled={submitting} sx={{ py: 1.5 }}>
                {submitting ? <CircularProgress size={24} /> : 'Login'}
              </Button>
            </form>
          </Paper>
        </Box>
      </Container>
    </>
  );
}
