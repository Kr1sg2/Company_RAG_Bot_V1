import React, { useEffect, useRef, useState } from "react";
import { fetchPublicBranding, type Branding } from "../lib/api";

/** ------------------------------------------------------------------
 *  Types and helpers
 *  ------------------------------------------------------------------ */
type Source = { name?: string; url?: string; file_link?: string };
type Chunk = { text: string; name?: string; file_link?: string };

type ChatReply =
  | { response: string; sources?: Source[] }
  | { response: Chunk[]; sources?: never };

type Normalized = {
  answer: string;
  sources: { label: string; href?: string }[];
};

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

function normalizeReply(payload: ChatReply): Normalized {
  // Case A: response is a string with optional sources[]
  if (typeof (payload as any)?.response === "string") {
    const answer = (payload as any).response as string;
    const sources = ((payload as any).sources ?? []) as Source[];
    return {
      answer,
      sources: sources.map((s) => ({
        label: s.name ?? s.url ?? s.file_link ?? "source",
        href: s.url ?? s.file_link,
      })),
    };
  }

  // Case B: response is an array of chunks [{text,...}]
  const arr = (payload as any).response as Chunk[];
  const answer = Array.isArray(arr) ? arr.map((x) => x.text).join("\n\n") : "";
  const sources =
    Array.isArray(arr)
      ? arr.slice(0, 3).map((x) => ({
          label: x.name ?? "source",
          href: x.file_link,
        }))
      : [];
  return { answer, sources };
}

function friendlyError(message: string) {
  const m = message.toLowerCase();
  if (m.includes("db error") || m.includes("compactor") || m.includes("500")) {
    return "The knowledge index is rebuilding or temporarily unavailable. Please try again in a minute.";
  }
  return "Sorry, I hit an error while contacting the assistant. Please try again.";
}

/** ------------------------------------------------------------------
 *  UI
 *  ------------------------------------------------------------------ */
type Msg = {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: { label: string; href?: string }[];
};

export default function ClientChat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [throttled, setThrottled] = useState(false);
  const [branding, setBranding] = useState<Branding | null>(null);
  const lastSentAtRef = useRef<number>(0);
  const listRef = useRef<HTMLDivElement>(null);

  // Load branding on mount
  useEffect(() => {
    fetchPublicBranding()
      .then(setBranding)
      .catch(() => console.warn("Failed to load branding, using defaults"));
  }, []);

  // Auto-scroll to latest
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    const now = Date.now();
    if (loading) return;
    if (!input.trim()) return;

    // Simple rate limit: 1 request / 750ms
    if (now - lastSentAtRef.current < 750) {
      setThrottled(true);
      setTimeout(() => setThrottled(false), 750);
      return;
    }
    lastSentAtRef.current = now;

    const userMsg: Msg = { id: crypto.randomUUID(), role: "user", text: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const r = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.text }),
      });

      if (!r.ok) {
        throw new Error(`${r.status} ${r.statusText}`);
      }

      const raw: ChatReply = await r.json();
      const { answer, sources } = normalizeReply(raw);

      const assistantMsg: Msg = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: answer || "No results found.",
        sources,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const assistantMsg: Msg = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: friendlyError(String(err?.message || err)),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  // Helper functions for branding styles
  const px = (n?: number, d = 0) => `${n ?? d}px`;
  const asDim = (v: unknown, d: string) => (typeof v === "number" ? `${v}px` : (typeof v === "string" && v.trim()) ? v : d);

  // Derive styles from branding
  const pageStyle: React.CSSProperties = {
    background: branding?.pageBackgroundUrl
      ? `url(${branding.pageBackgroundUrl}) center/cover no-repeat`
      : branding?.pageBackgroundColor ?? "#f8fafc",
    fontFamily: branding?.fontFamily ?? 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    minHeight: "100vh",
  };

  const cardStyle: React.CSSProperties = {
    maxWidth: asDim(branding?.chatWidth, "64rem"),
    borderRadius: asDim(branding?.cardRadius, "1rem"),
    backgroundColor: branding?.cardBackgroundColor ?? "rgba(255,255,255,0.9)",
    border: "1px solid rgb(226 232 240)",
    backdropFilter: "blur(8px)",
    padding: px(branding?.cardPadding, 0),
  };

  const titleStyle: React.CSSProperties = {
    fontSize: px(branding?.titleFontSize, 20),
    fontWeight: branding?.titleBold ? "600" : "normal",
    fontStyle: branding?.titleItalic ? "italic" : "normal",
    color: "#0f172a",
  };

  const taglineStyle: React.CSSProperties = {
    fontSize: px(branding?.taglineFontSize, 14),
    fontWeight: branding?.taglineBold ? "600" : "normal",
    fontStyle: branding?.taglineItalic ? "italic" : "normal",
    color: "#64748b",
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4" style={pageStyle}>
      <div className="w-full shadow-lg" style={cardStyle}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200">
          <h1 style={titleStyle}>{branding?.companyName ?? "Company Chat"}</h1>
          <p style={taglineStyle}>{branding?.taglineText ?? "Ask questions about your company documents."}</p>
        </div>

        {/* Messages */}
        <div 
          ref={listRef} 
          className="px-6 py-4 overflow-y-auto space-y-4"
          style={{ height: asDim(branding?.chatHeight, "60vh"), paddingTop: px(branding?.chatOffsetTop, 16) }}
        >
          {messages.length === 0 && (
            <div className="text-slate-500 text-sm">
              {branding?.emptyStateText ?? "Start by asking something like 'What is the company dress code?'"}
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className="text-sm whitespace-pre-wrap"
                style={{
                  maxWidth: `${branding?.bubbleMaxWidth ?? 70}%`,
                  borderRadius: asDim(branding?.bubbles?.radius, "1rem"),
                  padding: px(branding?.bubblePadding, 12),
                  backgroundColor: m.role === "user" 
                    ? branding?.bubbles?.userBg ?? "#4f46e5"
                    : branding?.bubbles?.aiBg ?? "#f1f5f9",
                  color: m.role === "user"
                    ? branding?.userTextColor ?? "#ffffff"
                    : branding?.aiTextColor ?? "#0f172a",
                  border: m.role === "user"
                    ? branding?.userBubbleBorder ?? "none"
                    : branding?.aiBubbleBorder ?? "none",
                  borderBottomRightRadius: m.role === "user" ? "4px" : undefined,
                  borderBottomLeftRadius: m.role === "assistant" ? "4px" : undefined,
                  marginBottom: px(branding?.messageSpacing, 16),
                }}
              >
                {m.text}

                {/* Sources (assistant only) */}
                {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-slate-200/70 text-xs text-slate-600">
                    <div className="font-semibold mb-1">Sources</div>
                    <ul className="list-disc pl-4 space-y-1">
                      {m.sources.slice(0, 5).map((s, i) => (
                        <li key={i}>
                          {s.href ? (
                            <a className="underline" href={s.href} target="_blank" rel="noreferrer">
                              {truncate(s.label, 80)}
                            </a>
                          ) : (
                            <span>{truncate(s.label, 80)}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-slate-500 text-sm">
              <span className="inline-block h-2 w-2 rounded-full bg-slate-400 animate-pulse"></span>
              Thinking…
            </div>
          )}
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-t border-slate-200">
          <div className="flex items-center gap-2">
            <input
              className="flex-1 px-4 border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              style={{
                height: px(branding?.inputHeight, 48),
                borderRadius: asDim(branding?.inputRadius, "0.75rem"),
              }}
              placeholder={branding?.inputPlaceholder ?? "Type your question and press Enter…"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || throttled || !input.trim()}
              className="text-white transition cursor-pointer"
              style={{
                height: px(branding?.inputHeight, 48),
                paddingLeft: "20px",
                paddingRight: "20px",
                borderRadius: asDim(branding?.inputRadius, "0.75rem"),
                backgroundColor: loading || throttled || !input.trim()
                  ? "#94a3b8"
                  : branding?.colors?.primary ?? "#4f46e5",
                cursor: loading || throttled || !input.trim() ? "not-allowed" : "pointer",
              }}
              title={throttled ? "Please wait a moment…" : "Send"}
              onMouseOver={(e) => {
                if (!loading && !throttled && input.trim()) {
                  (e.target as HTMLButtonElement).style.backgroundColor = branding?.colors?.accent ?? "#4338ca";
                }
              }}
              onMouseOut={(e) => {
                if (!loading && !throttled && input.trim()) {
                  (e.target as HTMLButtonElement).style.backgroundColor = branding?.colors?.primary ?? "#4f46e5";
                }
              }}
            >
              {loading ? "…" : "Send"}
            </button>
          </div>
          {throttled && <div className="mt-2 text-xs text-slate-500">Rate limit: please wait a moment.</div>}
        </div>
      </div>
    </div>
  );
}

/** utils */
function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}