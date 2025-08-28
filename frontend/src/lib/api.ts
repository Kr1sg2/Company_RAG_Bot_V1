const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8600";

export type Branding = {
  companyName: string;
  taglineText?: string;
  emptyStateText?: string;
  inputPlaceholder?: string;
  logoDataUrl?: string | null;
  faviconUrl?: string | null;
  pageBackgroundUrl?: string | null;
  chatCardBackgroundUrl?: string | null;
  colors: { primary: string; accent: string; bg: string; text: string };
  bubbles: { radius: string; aiBg: string; userBg: string };
  chatWidth: string;
  chatHeight: string;
  chatOffsetTop: string;
  cardRadius: string;
  cardBg: string;
};

export async function fetchPublicBranding(): Promise<Branding> {
  const res = await fetch(`${API_BASE}/api/admin/settings/public/branding`);
  if (!res.ok) throw new Error(`branding ${res.status}`);
  return res.json();
}

export async function getAdminBranding(auth: string): Promise<Branding> {
  const res = await fetch(`${API_BASE}/api/admin/settings/branding`, {
    headers: { Authorization: `Basic ${auth}` },
  });
  if (!res.ok) throw new Error(`admin branding ${res.status}`);
  return res.json();
}

export async function putAdminBranding(auth: string, payload: Partial<Branding>): Promise<Branding> {
  const res = await fetch(`${API_BASE}/api/admin/settings/branding`, {
    method: "PUT",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`put branding ${res.status}`);
  return res.json();
}

export async function chat(query: string): Promise<{ response: string; sources?: any[] }> {
  const res = await fetch(`${API_BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`chat ${res.status}`);
  return res.json();
}