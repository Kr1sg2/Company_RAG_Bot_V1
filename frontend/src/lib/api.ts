import { Branding } from './brandingTypes';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export async function fetchPublicBranding(): Promise<Branding> {
  const res = await fetch(`${API_BASE}/api/admin/settings/public/branding`);
  if (!res.ok) throw new Error(`branding ${res.status}`);
  return res.json();
}

export async function getAdminBranding(auth: string): Promise<Branding> {
  const res = await fetch(`${API_BASE}/admin/settings/branding`, {
    headers: { Authorization: `Basic ${auth}` },
  });
  if (!res.ok) throw new Error(`admin branding ${res.status}`);
  return res.json();
}

export async function putAdminBranding(auth: string, payload: Partial<Branding>): Promise<Branding> {
  const res = await fetch(`${API_BASE}/admin/settings/branding`, {
    method: "PUT",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`put branding ${res.status}: ${errorText}`);
  }
  return res.json();
}

// Chat API types for better error handling
export type ChatSource = {
  name?: string;
  url?: string;
  file_link?: string;
};

export type ChatChunk = {
  text: string;
  name?: string;
  file_link?: string;
};

export type ChatReply = 
  | { response: string; sources?: ChatSource[] }
  | { response: ChatChunk[]; sources?: never };

export type NormalizedChatReply = {
  answer: string;
  sources: { label: string; href?: string }[];
};

// Enhanced chat function with better error handling
export async function chat(message: string): Promise<NormalizedChatReply> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`chat ${res.status}: ${errorText}`);
  }
  
  const raw: ChatReply = await res.json();
  return normalizeChatReply(raw);
}

// Normalize different response formats
export function normalizeChatReply(payload: ChatReply): NormalizedChatReply {
  // Case A: response is a string with optional sources[]
  if (typeof (payload as any)?.response === "string") {
    const answer = (payload as any).response as string;
    const sources = ((payload as any).sources ?? []) as ChatSource[];
    return {
      answer,
      sources: sources.map((s) => ({
        label: s.name ?? s.url ?? s.file_link ?? "source",
        href: s.url ?? s.file_link,
      })),
    };
  }

  // Case B: response is an array of chunks [{text,...}]
  const arr = (payload as any).response as ChatChunk[];
  const answer = Array.isArray(arr) ? arr.map((x) => x.text).join("\n\n") : "";
  const sources = Array.isArray(arr)
    ? arr.slice(0, 5).map((x) => ({
        label: x.name ?? "source",
        href: x.file_link,
      }))
    : [];
  return { answer, sources };
}

// Friendly error messages
export function friendlyError(message: string): string {
  const m = message.toLowerCase();
  if (m.includes("db error") || m.includes("compactor") || m.includes("500")) {
    return "The knowledge index is rebuilding or temporarily unavailable. Please try again in a minute.";
  }
  if (m.includes("401") || m.includes("unauthorized")) {
    return "Authentication required. Please log in.";
  }
  if (m.includes("429") || m.includes("rate limit")) {
    return "Too many requests. Please wait a moment before trying again.";
  }
  return "Sorry, I hit an error while contacting the assistant. Please try again.";
}