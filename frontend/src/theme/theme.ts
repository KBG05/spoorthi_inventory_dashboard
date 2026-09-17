import { alpha, createTheme } from '@mui/material/styles';
import type { ThemeOptions } from '@mui/material/styles';

// Light Theme - premium, calm, and business-ready
const lightPalette = {
  primary: {
    main: '#405b82',
    light: '#5c77a0',
    dark: '#2d4362',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#5578a4',
    light: '#7392b9',
    dark: '#3f5e81',
    contrastText: '#ffffff',
  },
  success: {
    main: '#2d8659',
    light: '#5fa97b',
    dark: '#1f5f40',
    contrastText: '#ffffff',
  },
  error: {
    main: '#b84a42',
    light: '#d47470',
    dark: '#8a3531',
    contrastText: '#ffffff',
  },
  warning: {
    main: '#d4893d',
    light: '#e2a75f',
    dark: '#a86a2c',
    contrastText: '#ffffff',
  },
  info: {
    main: '#3b5275',
    light: '#5673a0',
    dark: '#293d5c',
    contrastText: '#ffffff',
  },
  background: {
    default: '#eff3f8',
    paper: '#f8fbff',
  },
  text: {
    primary: '#1f2d42',
    secondary: '#51627c',
    disabled: 'rgba(31, 45, 66, 0.4)',
  },
  divider: 'rgba(64, 91, 130, 0.14)',
};

// Dark Theme reference palette
const darkPalette = {
  primary: {
    main: '#6e9ac8',
    light: '#90b4d8',
    dark: '#4d79a8',
    contrastText: '#0d1520',
  },
  secondary: {
    main: '#7aaec8',
    light: '#98c4db',
    dark: '#5590ae',
    contrastText: '#0a1820',
  },
  success: {
    main: '#5fa97b',
    light: '#7dbf9b',
    dark: '#3e8659',
    contrastText: '#0d1e16',
  },
  error: {
    main: '#e07070',
    light: '#f08f8f',
    dark: '#b84a42',
    contrastText: '#1c0e0e',
  },
  warning: {
    main: '#f0ad4e',
    light: '#f5c366',
    dark: '#d4893d',
    contrastText: '#1a1408',
  },
  info: {
    main: '#6e9ac8',
    light: '#90b4d8',
    dark: '#4d79a8',
    contrastText: '#0d1520',
  },
  background: {
    default: '#0e1420',
    paper: '#18202e',
  },
  text: {
    primary: '#dce6f5',
    secondary: '#8aa4c2',
    disabled: 'rgba(220, 230, 245, 0.4)',
  },
  divider: 'rgba(110, 154, 200, 0.16)',
};

// Common theme options
const getCommonThemeOptions = (mode: 'light' | 'dark'): ThemeOptions => {
  const palette = mode === 'light' ? lightPalette : darkPalette;

  return {
  palette: {
    mode,
    ...palette,
  },
  typography: {
    fontFamily: '"Manrope", "Source Sans 3", sans-serif',
    h1: {
      fontSize: 'clamp(2rem, 3vw, 2.6rem)',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: 'clamp(1.7rem, 2.2vw, 2.15rem)',
      fontWeight: 700,
      lineHeight: 1.24,
    },
    h3: {
      fontSize: 'clamp(1.35rem, 1.7vw, 1.8rem)',
      fontWeight: 700,
      lineHeight: 1.28,
    },
    h4: {
      fontSize: 'clamp(1.15rem, 1.3vw, 1.45rem)',
      fontWeight: 700,
      lineHeight: 1.34,
    },
    h5: {
      fontSize: '1.1rem',
      fontWeight: 650,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '0.98rem',
      fontWeight: 650,
      lineHeight: 1.46,
    },
    subtitle1: {
      fontSize: '0.98rem',
      fontWeight: 500,
      lineHeight: 1.6,
    },
    subtitle2: {
      fontSize: '0.88rem',
      fontWeight: 600,
      lineHeight: 1.54,
    },
    body1: {
      fontSize: '0.96rem',
      fontWeight: 400,
      lineHeight: 1.66,
    },
    body2: {
      fontSize: '0.87rem',
      fontWeight: 400,
      lineHeight: 1.6,
    },
    button: {
      fontWeight: 600,
      letterSpacing: '0.01em',
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage: mode === 'light'
            ? 'radial-gradient(circle at 10% -15%, rgba(64, 91, 130, 0.1), transparent 42%), radial-gradient(circle at 92% 6%, rgba(85, 120, 164, 0.09), transparent 38%)'
            : 'radial-gradient(circle at 8% -10%, rgba(30, 55, 90, 0.50), transparent 45%)',
        },
        '.MuiDataGrid-columnHeaders': {
          // backgroundColor: mode === 'light' ? alpha(palette.primary.main, 0.1) : alpha(palette.primary.main, 0.2),
          // borderBottom: `1px solid ${alpha(palette.primary.main, mode === 'light' ? 0.24 : 0.32)}`,
        },
        '.MuiDataGrid-columnHeaderTitle': {
          color: '#C1121F',
          fontWeight: 900,
          fontVariationSettings: '"wght" 900',
          fontSize: '0.825rem',
          letterSpacing: '0.02em',
          textTransform: 'uppercase',
          textAlign: 'left',
        },
        '.MuiDataGrid-columnHeaderTitleContainer': {
          justifyContent: 'flex-start',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          boxShadow: mode === 'light' 
            ? '0 4px 16px rgba(28, 35, 60, 0.08)'
            : '0 4px 14px rgba(0, 0, 8, 0.36)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: mode === 'light' ? '#e8eef6' : '#111826',
          color: mode === 'light' ? '#344964' : '#c8d8ef',
          borderRight: `1px solid ${mode === 'light' ? 'rgba(64, 91, 130, 0.18)' : palette.divider}`,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: palette.background.paper,
          border: `1px solid ${palette.divider}`,
          borderRadius: 14,
          boxShadow: mode === 'light'
            ? '0 6px 20px rgba(28, 35, 60, 0.06)'
            : '0 6px 18px rgba(4, 8, 20, 0.34)',
          transition: 'transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: palette.background.paper,
          border: `1px solid ${palette.divider}`,
          borderRadius: 14,
        },
        elevation1: {
          boxShadow: mode === 'light'
            ? '0 6px 18px rgba(28, 35, 60, 0.06)'
            : '0 5px 16px rgba(0, 0, 0, 0.32)',
        },
        elevation2: {
          boxShadow: mode === 'light'
            ? '0 8px 24px rgba(28, 35, 60, 0.09)'
            : '0 8px 22px rgba(0, 0, 0, 0.36)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 999,
          paddingInline: '1rem',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: `0 6px 16px ${alpha(palette.primary.main, 0.24)}`,
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiListSubheader: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
          color: mode === 'light' ? 'rgba(52, 73, 102, 0.68)' : 'rgba(138, 164, 194, 0.7)',
          fontSize: '0.68rem',
          fontWeight: 700,
          letterSpacing: '0.10em',
          textTransform: 'uppercase',
          lineHeight: 1.8,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          height: 6,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${palette.divider}`,
        },
        head: {
          color: '#C1121F',
          fontWeight: 900,
          fontVariationSettings: '"wght" 900',
          fontSize: '0.925rem',
          letterSpacing: '0.02em',
          textTransform: 'uppercase',
          textAlign: 'left',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: '0.76rem',
          borderRadius: 8,
          backgroundColor: mode === 'light' ? '#1c2333' : '#dce6f5',
          color: mode === 'light' ? '#dce6f5' : '#1c2333',
        },
      },
    },
  },
  };
};

// Create themes
export const lightTheme = createTheme(getCommonThemeOptions('light'));
export const darkTheme = createTheme(getCommonThemeOptions('dark'));

// Export a function to get theme by mode
export const getTheme = (mode: 'light' | 'dark') => {
  return mode === 'light' ? lightTheme : darkTheme;
};
