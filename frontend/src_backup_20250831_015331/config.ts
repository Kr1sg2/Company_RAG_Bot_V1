// src/config.ts
const RAW =
  (import.meta.env.VITE_API_BASE as string | undefined) || window.location.origin;

// Remove trailing slashes and a trailing /api if present
export const API_BASE = RAW.replace(/\/+$/, '').replace(/\/api$/, '');

export function apiUrl(path: string) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return p.startsWith('/api') ? `${API_BASE}${p}` : `${API_BASE}/api${p}`;
}
