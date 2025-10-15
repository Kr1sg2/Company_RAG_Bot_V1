export type ChatRequest = { message: string };
export type ChatSource = { title?: string; url?: string; snippet?: string };
export type ChatResponse = { answer: string; sources?: ChatSource[] };

export async function chat(req: ChatRequest, signal?: AbortSignal): Promise<ChatResponse>;
export async function chat(message: string, options?: { system?: string }): Promise<ChatResponse & { reply: string }>;
export async function chat(
  reqOrMessage: ChatRequest | string,
  signalOrOptions?: AbortSignal | { system?: string }
): Promise<ChatResponse & { reply?: string }> {
  const base = import.meta.env.VITE_API_BASE || "/api";
  
  let body: any;
  let signal: AbortSignal | undefined;
  
  if (typeof reqOrMessage === "string") {
    // Old calling pattern: chat(message, { system: ... })
    body = { message: reqOrMessage };
    if (signalOrOptions && typeof signalOrOptions === "object" && "system" in signalOrOptions) {
      body.systemPrompt = signalOrOptions.system;
    }
  } else {
    // New calling pattern: chat({ message: ... }, signal)
    body = reqOrMessage;
    if (signalOrOptions && "aborted" in signalOrOptions) {
      signal = signalOrOptions as AbortSignal;
    }
  }
  
  const r = await fetch(`${base}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const result = await r.json();
  
  // Make sure we have both answer and reply for backward compatibility
  const answer = result.answer || result.reply || result.response || "";
  return {
    answer,
    reply: answer,
    sources: result.sources
  };
}

// Add backward compatibility for other functions that existing components use
export async function fetchPublicBranding(): Promise<any> {
  // Return minimal branding to prevent errors
  return {
    companyName: "Company Chat",
    taglineText: "Ask questions about your company documents.",
    logoDataUrl: null,
    systemPrompt: null
  };
}

export async function getAdminBranding(_auth?: string): Promise<any> {
  // Stub implementation for admin functionality
  console.warn("Admin branding functionality requires the full API implementation");
  return {};
}

export async function putAdminBranding(_auth: any, _data: any): Promise<any> {
  // Stub implementation for admin functionality  
  console.warn("Admin branding functionality requires the full API implementation");
  return {};
}