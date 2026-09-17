import { useState, type MouseEvent } from 'react';
import { Outlet } from 'react-router-dom';
import { AppBar, Box, Divider, IconButton, Menu, MenuItem, Toolbar, Typography } from '@mui/material';
import { AccountCircle, Brightness4, Brightness7, Logout } from '@mui/icons-material';
import { Sidebar } from '../components/Sidebar';
import { useAuth } from '../contexts/AuthContext';
import { useThemeMode } from '../theme/ThemeProvider';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { mode, toggleTheme } = useThemeMode();
  const { user, logout } = useAuth();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  const handleMenuOpen = (event: MouseEvent<HTMLElement>) => setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);
  const handleLogout = () => {
    handleMenuClose();
    logout();
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default', overflow: 'hidden' }}>
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen((prev) => !prev)} />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          height: '100vh',
          overflow: 'hidden',
        }}
      >
        <AppBar
          position="sticky"
          elevation={0}
          sx={{
            borderRadius: 0,
            bgcolor: 'background.paper',
            color: 'text.primary',
            borderBottom: 1,
            borderColor: 'divider',
          }}
        >
          <Toolbar sx={{ minHeight: 64, px: { xs: 2, sm: 3 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: 50,
                  px: 1.75,
                  mr: 1.5,
                  borderRadius: 1.5,
                  bgcolor: mode === 'light' ? 'rgba(64, 91, 130, 0.1)' : 'rgba(255, 255, 255, 0.5)',
                  border: '1px solid',
                  borderColor: mode === 'light' ? 'rgba(64, 91, 130, 0.25)' : 'rgba(255, 255, 255, 0.3)',
                }}
              >
                <img src="/Spoorthi-Logo.png" alt="Spoorthi Logo" style={{ height: 40, width: 'auto', display: 'block' }} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Raw Material Inventory
              </Typography>
            </Box>
            <Box sx={{ flexGrow: 1 }} />
            <IconButton onClick={toggleTheme} color="inherit" sx={{ mr: 1 }}>
              {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
            <IconButton onClick={handleMenuOpen} color="inherit">
              <AccountCircle />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={menuOpen}
              onClose={handleMenuClose}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Logged in as
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {user?.username}
                </Typography>
              </Box>
              <Divider />
              <MenuItem onClick={handleLogout}>
                <Logout fontSize="small" sx={{ mr: 1.5 }} />
                Logout
              </MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>

        <Box
          sx={{
            flexGrow: 1,
            p: 2.5,
            width: '100%',
            boxSizing: 'border-box',
            overflow: 'hidden auto',
          }}
        >
          <Outlet />
        </Box>

        <Box
          component="footer"
          sx={{
            py: 2,
            px: 3,
            mt: 'auto',
            borderTop: 1,
            borderColor: 'divider',
            bgcolor: 'background.paper',
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" color="text.primary" sx={{ fontWeight: 500 }}>
            © Copyright {new Date().getFullYear()} Lumin AI Systems
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
