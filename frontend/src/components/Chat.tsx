import { useEffect, useMemo, useRef, useState } from "react";
import type { ChatRequest, ChatResponse } from "../lib/api";
import { chat } from "../lib/api";

const LS_KEY = "chat_recent_questions_v1";
const MAX_RECENT = 3;

export default function Chat() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [recent, setRecent] = useState<string[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setRecent(parsed.slice(0, MAX_RECENT).filter((x): x is string => typeof x === "string"));
        }
      }
    } catch {
      // ignore
    }
  }, []);

  const saveRecent = (q: string) => {
    const next = [q, ...recent.filter((x) => x !== q)].slice(0, MAX_RECENT);
    setRecent(next);
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(next));
    } catch {
      // ignore
    }
  };

  const canSend = useMemo(() => {
    return !loading && input.trim().length > 0;
  }, [loading, input]);

  const onSend = async (message?: string) => {
    const msg = (message ?? input).trim();
    if (!msg || loading) return;

    setError(null);
    setResponse(null);
    setLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await chat({ message: msg } as ChatRequest, controller.signal);
      setResponse(res);
      saveRecent(msg);
    } catch (e) {
      if ((e as any)?.name === "AbortError") {
        setError("Request aborted.");
      } else {
        setError(e instanceof Error ? e.message : "Request failed.");
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  };

  const onAbort = () => {
    abortRef.current?.abort();
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void onSend();
    }
  };

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  return (
    <section style={{ padding: "1rem", borderTop: "1px solid #e5e7eb" }}>
      <h2 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "0.5rem" }}>
        Chat
      </h2>

      <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-start" }}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a question…"
          rows={3}
          style={{
            flex: 1,
            padding: "0.5rem",
            fontSize: "0.95rem",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            resize: "vertical",
          }}
        />
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={() => onSend()}
            disabled={!canSend}
            style={{
              padding: "0.5rem 0.75rem",
              background: canSend ? "var(--brand-primary, #2563eb)" : "#93c5fd",
              color: "white",
              border: "none",
              borderRadius: 6,
              cursor: canSend ? "pointer" : "not-allowed",
            }}
            aria-disabled={!canSend}
          >
            {loading ? "Asking…" : "Ask"}
          </button>
          {loading && (
            <button
              type="button"
              onClick={onAbort}
              style={{
                padding: "0.5rem 0.75rem",
                background: "#ef4444",
                color: "white",
                border: "none",
                borderRadius: 6,
                cursor: "pointer",
              }}
            >
              Abort
            </button>
          )}
        </div>
      </div>

      {recent.length > 0 && (
        <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {recent.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => {
                setInput(q);
                void onSend(q);
              }}
              style={{
                padding: "0.25rem 0.5rem",
                border: "1px solid #cbd5e1",
                background: "white",
                borderRadius: 9999,
                cursor: "pointer",
                fontSize: "0.875rem",
              }}
              title="Ask again"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {error && (
        <p role="alert" style={{ color: "#b91c1c", marginTop: "0.75rem" }}>
          {error}
        </p>
      )}

      {response && (
        <div style={{ marginTop: "1rem", borderTop: "1px solid #e5e7eb", paddingTop: "0.75rem" }}>
          <div style={{ whiteSpace: "pre-wrap" }}>{response.answer}</div>
          {Array.isArray(response.sources) && response.sources.length > 0 && (
            <div style={{ marginTop: "0.75rem" }}>
              <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>Sources</div>
              <ul style={{ paddingLeft: "1rem", listStyle: "disc" }}>
                {response.sources.map((s, idx) => (
                  <li key={idx} style={{ marginBottom: "0.25rem" }}>
                    {s.url ? (
                      <a href={s.url} target="_blank" rel="noreferrer">
                        {s.title || s.url}
                      </a>
                    ) : (
                      <span>{s.title || "Source"}</span>
                    )}
                    {s.snippet ? <div style={{ color: "#475569" }}>{s.snippet}</div> : null}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}