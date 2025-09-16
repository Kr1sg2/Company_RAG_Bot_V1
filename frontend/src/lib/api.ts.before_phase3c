import { apiUrl } from '../config';
import type { Branding } from './brandingTypes';

// --- Types used by the chat client ------------------------------------------------
export type ChatRole = 'system' | 'user' | 'assistant';
export interface ChatMessage { role: ChatRole; content: string; }

// Keep `answer?` for compatibility with ClientChat.tsx which may read response.answer
export interface ChatResponse {
  reply: string;
  answer?: string;
  sources?: any[];
}

// --- Helpers ----------------------------------------------------------------------
function ok<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status} ${res.statusText}`);
    (err as any).status = res.status;
    throw err;
  }
  return res.json() as Promise<T>;
}

export function friendlyError(err: unknown): string {
  if (typeof err === 'string') return err;
  if (err instanceof Error) {
    const code = (err as any)?.status;
    if (code === 401) return 'Unauthorized — please log in.';
    if (code === 403) return 'Forbidden — your account lacks access.';
    if (code === 404) return 'Not found — the endpoint may be disabled.';
    return err.message || 'Unexpected error.';
  }
  try { return JSON.stringify(err); } catch { return 'Unexpected error.'; }
}

function authHeaders(auth?: string): HeadersInit {
  return auth
    ? { Authorization: `Basic ${auth}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' };
}

// --- Branding endpoints -----------------------------------------------------------
// apiUrl() will prefix `/api` automatically when needed.
// Passing '/admin/branding' -> '/api/admin/branding', etc.

function normalizeBranding(raw: any): Branding {
  const b = raw || {};
  const llm = b.llm || {};
  return {
    ...b,
    aiSystemPrompt: b.aiSystemPrompt ?? b.systemPrompt ?? llm.systemPrompt ?? "",
    model: b.model ?? llm.model ?? "gpt-4o-mini",
    temperature: b.temperature ?? llm.temperature ?? 0.7,
    top_p: b.top_p ?? llm.top_p ?? 1,
    max_tokens: b.max_tokens ?? llm.max_tokens ?? 512,
    frequency_penalty: b.frequency_penalty ?? llm.frequency_penalty ?? 0,
    presence_penalty: b.presence_penalty ?? llm.presence_penalty ?? 0,
    strictness: b.strictness ?? llm.strictness ?? 5,
    responseFormat: b.responseFormat ?? "paragraphs",
  } as Branding;
}

/** Public branding (no auth). GET /api/admin/settings/public/branding */
export async function fetchPublicBranding(): Promise<Branding> {
  const res = await fetch(apiUrl('/admin/settings/public/branding'), {
    credentials: 'include',
    cache: 'no-store',
  });
  const raw = await ok<any>(res);
  return normalizeBranding(raw);
}

/** Admin branding (auth required). GET /api/admin/settings/branding */
export async function getAdminBranding(auth: string): Promise<Branding> {
  const res = await fetch(apiUrl('/admin/settings/branding'), {
    method: 'GET',
    headers: authHeaders(auth),
    credentials: 'include',
  });
  const raw = await ok<any>(res);
  return normalizeBranding(raw);
}

/** Save branding. PUT /api/admin/settings/branding */
export async function putAdminBranding(
  auth: string,
  body: Branding
): Promise<Branding> {
  const out: any = { ...body };
  if (typeof out.llm !== "object" || out.llm === null) out.llm = {};
  
  // mirror fields to both top level and llm object for compatibility
  out.llm.systemPrompt = out.aiSystemPrompt ?? "";
  out.llm.model = out.model;
  out.llm.temperature = out.temperature;
  out.llm.top_p = out.top_p;
  out.llm.max_tokens = out.max_tokens;
  out.llm.frequency_penalty = out.frequency_penalty;
  out.llm.presence_penalty = out.presence_penalty;
  out.llm.strictness = out.strictness;
  
  // never send any 'allowWeb' or 'tools' flags
  delete out.allowWeb;
  delete out.tools;
  delete out.tool_choice;
  
  const res = await fetch(apiUrl('/admin/settings/branding'), {
    method: 'PUT', 
    headers: authHeaders(auth),
    credentials: 'include',
    body: JSON.stringify(out)
  });
  
  const saved = await ok<any>(res);
  return normalizeBranding(saved);
}

// --- Chat endpoint(s) -------------------------------------------------------------
// Robust POST JSON to /api/chat with fallback to /api/chat/ if 404
export async function chat(userText: string, opts?: { system?: string }): Promise<ChatResponse> {
  const controller = new AbortController();
  const payload: any = { message: userText };

  // pass custom system prompt if admin set one or caller passes one
  if (opts?.system) payload.systemPrompt = opts.system;

  // ALSO: if you already loaded public branding into memory and it has systemPrompt,
  // set payload.systemPrompt ??= branding.systemPrompt;
  try {
    const branding = await fetchPublicBranding();
    if (branding?.systemPrompt && !payload.systemPrompt) {
      payload.systemPrompt = branding.systemPrompt;
    }
  } catch {
    // If branding fetch fails, continue without it
  }

  // Ensure we never send any web/tool-related flags (locked to closed RAG)
  payload.tools = [];
  payload.tool_choice = "none";
  delete payload.allowWeb;
  delete payload.enableWeb;

  async function postTo(path: string) {
    const r = await fetch(apiUrl(path), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      signal: controller.signal,
      body: JSON.stringify(payload),
    });
    if (r.status === 404) throw new Error('TRY_FALLBACK');
    return ok<any>(r);
  }

  try {
    try { 
      const j = await postTo('/chat'); 
      const reply = j?.reply ?? j?.response ?? j?.content ?? j?.message ?? (typeof j === 'string' ? j : '');
      const sources = j?.sources ?? j?.data?.sources ?? j?.context?.sources ?? [];
      return { reply, answer: reply, sources };
    }
    catch (e: any) {
      if (String(e?.message) === 'TRY_FALLBACK') {
        const j = await postTo('/chat/');
        const reply = j?.reply ?? j?.response ?? j?.content ?? j?.message ?? (typeof j === 'string' ? j : '');
        const sources = j?.sources ?? j?.data?.sources ?? j?.context?.sources ?? [];
        return { reply, answer: reply, sources };
      }
      throw e;
    }
  } finally {
    // Cleanup if needed
  }
}
