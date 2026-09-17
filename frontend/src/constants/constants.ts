export const ABC_COLORS: Record<string, string> = {
  A: '#00C853',
  B: '#FF6D00',
  C: '#FF1744',
  Overall: '#2979FF',
  Unknown: '#90A4AE',
};

export const XYZ_COLORS: Record<string, string> = {
  X: '#00C853',
  Y: '#FF6D00',
  Z: '#FF1744',
};

export const ABC_XYZ_COLORS: Record<string, string> = {
  AX: '#00C853',
  AY: '#00C853',
  AZ: '#00C853',
  BX: '#FF6D00',
  BY: '#FF6D00',
  BZ: '#FF6D00',
  CX: '#FF1744',
  CY: '#FF1744',
  CZ: '#FF1744',
};

export const DRAWER_WIDTH = {
  EXPANDED: 280,
  COLLAPSED: 60,
};

export function formatCurrencyCr(value: number): string {
  return `₹${(value / 10000000).toFixed(2)} Cr`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-IN').format(value);
}
