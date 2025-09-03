/**
 * Color utility functions for branding
 */

export const hexToRgba = (hex: string, alpha: number) => {
  const h = (hex || '#000').replace('#', '');
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h.padEnd(6,'0');
  const n = parseInt(full, 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const a = Math.max(0, Math.min(1, alpha ?? 1));
  return `rgba(${r}, ${g}, ${b}, ${a})`;
};

export const floatToPct = (v?: number) =>
  v == null ? '' : Math.round(Math.max(0, Math.min(1, v)) * 100);

export const pctToFloat = (x?: number|string) => {
  const n = Number(x);
  if (!Number.isFinite(n)) return undefined;
  return Math.max(0, Math.min(100, n)) / 100;
};

export const css = (v: string|number|undefined, fb='') =>
  v == null || v === '' ? fb : String(v);