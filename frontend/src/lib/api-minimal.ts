export type ChatRequest = { message: string };
export type ChatSource = { title?: string; url?: string; snippet?: string };
export type ChatResponse = { answer: string; sources?: ChatSource[] };

export async function chat(req: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  const base = import.meta.env.VITE_API_BASE || "/api";
  const r = await fetch(`${base}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}