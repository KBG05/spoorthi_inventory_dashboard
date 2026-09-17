import { NavLink } from 'react-router-dom';
import {
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  CloudSync as CloudSyncIcon,
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { DRAWER_WIDTH } from '../constants/constants';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactElement;
}

const navItems: NavItem[] = [
  { path: '/raw-materials', label: 'Raw Materials', icon: <DashboardIcon /> },
  { path: '/raw-materials/trend', label: 'Trend Analysis', icon: <TrendingUpIcon /> },
  { path: '/raw-materials/status', label: 'Ingestion Status', icon: <CloudSyncIcon /> },
];

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
}

export function Sidebar({ open, onToggle }: SidebarProps) {
  const theme = useTheme();
  const activeAccent = theme.palette.mode === 'light' ? '#405b82' : '#6e9ac8';
  const activeText = theme.palette.mode === 'light' ? '#2d4362' : '#dce6f5';

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: open ? DRAWER_WIDTH.EXPANDED : DRAWER_WIDTH.COLLAPSED,
        flexShrink: 0,
        transition: 'width 250ms ease-in-out',
        '& .MuiDrawer-paper': {
          width: open ? DRAWER_WIDTH.EXPANDED : DRAWER_WIDTH.COLLAPSED,
          boxSizing: 'border-box',
          transition: 'width 250ms ease-in-out',
          overflowX: 'hidden',
        },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: open ? 'flex-end' : 'center',
          p: 1,
          minHeight: 64,
        }}
      >
        <IconButton
          onClick={onToggle}
          size="small"
          aria-label={open ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          {open ? <ChevronLeftIcon /> : <ChevronRightIcon />}
        </IconButton>
      </Box>

      <Divider />

      <List sx={{ pt: 0.5, pb: 1.5 }}>
        {navItems.map((item) => (
          <Tooltip key={item.path} title={open ? '' : item.label} placement="right" arrow>
            <ListItem disablePadding sx={{ display: 'block' }}>
              <NavLink to={item.path} end style={{ textDecoration: 'none', color: 'inherit' }}>
                {({ isActive }: { isActive: boolean }) => (
                  <ListItemButton
                    sx={{
                      minHeight: 46,
                      justifyContent: open ? 'initial' : 'center',
                      px: 1.5,
                      mx: 0.9,
                      my: 0.5,
                      borderRadius: 2,
                      borderLeft: `3px solid ${isActive ? activeAccent : alpha(activeAccent, 0)}`,
                      backgroundColor: isActive
                        ? alpha(activeAccent, theme.palette.mode === 'light' ? 0.18 : 0.24)
                        : 'transparent',
                      color: isActive ? activeText : theme.palette.text.secondary,
                      transition: 'all 220ms ease',
                      '&:hover': {
                        backgroundColor: isActive
                          ? alpha(activeAccent, theme.palette.mode === 'light' ? 0.24 : 0.32)
                          : alpha(activeAccent, theme.palette.mode === 'light' ? 0.1 : 0.16),
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        mr: open ? 1.5 : 'auto',
                        justifyContent: 'center',
                        color: isActive ? activeText : theme.palette.text.secondary,
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      sx={{
                        opacity: open ? 1 : 0,
                        whiteSpace: 'nowrap',
                        '& .MuiTypography-root': {
                          fontWeight: isActive ? 700 : 500,
                          fontSize: '0.88rem',
                        },
                      }}
                    />
                  </ListItemButton>
                )}
              </NavLink>
            </ListItem>
          </Tooltip>
        ))}
      </List>
    </Drawer>
  );
}
