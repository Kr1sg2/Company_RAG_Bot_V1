/**
 * Color utility functions for branding
 */

export const hexToRgba = (hex: string, alpha: number): string => {
  const h = (hex || '#000000').replace('#', '');
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h;
  const n = parseInt(full, 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  const a = Math.max(0, Math.min(1, alpha ?? 1));
  return `rgba(${r}, ${g}, ${b}, ${a})`;
};

export const floatToPct = (v?: number): number => {
  return v == null ? 100 : Math.round(v * 100);
};

export const pctToFloat = (p?: number | string): number => {
  const n = Number(p);
  if (!Number.isFinite(n)) return 1;
  return Math.max(0, Math.min(100, n)) / 100;
};

/**
 * Convert CSS size value to string
 */
export const toCssSize = (value: string | number | undefined, fallback = '1rem'): string => {
  if (typeof value === 'number') return `${value}px`;
  if (typeof value === 'string' && value.trim()) return value;
  return fallback;
};

/**
 * Ensure a value is a valid percentage string
 */
export const toPercentage = (value: string | number | undefined, fallback = '100'): string => {
  if (typeof value === 'number') return `${value}%`;
  if (typeof value === 'string' && value.trim()) {
    // If it's already a percentage, return as is
    if (value.includes('%')) return value;
    // Otherwise treat as a number
    const num = parseFloat(value);
    if (Number.isFinite(num)) return `${num}%`;
  }
  return `${fallback}%`;
};