import { useEffect, useMemo, useState } from "react";
import { getSettings } from "@/lib/api";
import {
  BrandingSettings,
  defaultBranding,
  normalizeBranding,
  applyBrandingToDOM,
} from "@/lib/theme";
import SimpleChat from "@/components/SimpleChat";

// map url-ish value to CSS background-image value
function toCssUrl(v?: string | null) {
  if (!v) return "none";
  const s = String(v).trim().toLowerCase();
  return s === "none" ? "none" : `url(${v})`;
}

// set/clear the favicon <link> robustly
function applyFavicon(url?: string | null) {
  const head = document.head || document.getElementsByTagName("head")[0];
  // Remove any existing icons first
  for (const el of Array.from(
    head.querySelectorAll<HTMLLinkElement>('link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]')
  )) {
    el.parentNode?.removeChild(el);
  }
  // If we have a url, add a fresh <link rel="icon">
  const clean = (url ?? "").trim();
  if (clean) {
    const link = document.createElement("link");
    link.rel = "icon";
    link.href = clean;
    head.appendChild(link);
  }
}

export default function ClientChatPage() {
  const [branding, setBranding] = useState<BrandingSettings>(defaultBranding);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        // fetch public settings
        const raw = await getSettings({ publicOnly: true });

        // harden: coerce "" / "none" → null for the two background URLs
        const normalized = normalizeBranding({
          ...raw,
          pageBackgroundUrl:
            raw?.pageBackgroundUrl && String(raw.pageBackgroundUrl).trim().toLowerCase() !== "none"
              ? raw.pageBackgroundUrl
              : null,
          chatCardBackgroundUrl:
            raw?.chatCardBackgroundUrl && String(raw.chatCardBackgroundUrl).trim().toLowerCase() !== "none"
              ? raw.chatCardBackgroundUrl
              : null,
        });

        if (!alive) return;

        // apply CSS vars (colors + images)
        applyBrandingToDOM(normalized);

        // force the two bg image vars explicitly (so baked images can’t reappear)
        const root = document.documentElement.style;
        root.setProperty("--page-bg-url", toCssUrl(normalized.pageBackgroundUrl));
        root.setProperty("--chat-card-bg-image", toCssUrl(normalized.chatCardBackgroundUrl));

        // nuke any inline <body> background if page URL cleared
        if (!normalized.pageBackgroundUrl) {
          document.body.style.backgroundImage = "none";
        }

        // browser tab title
        if (normalized.companyName) {
          document.title = normalized.companyName;
        }

        // favicon (set or clear)
        applyFavicon(normalized.faviconUrl ?? null);

        setBranding(normalized);
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();

    // re-apply when the admin screen broadcasts a save
    const onUpdated = () => load();
    window.addEventListener("lexa:settings-updated", onUpdated);

    return () => {
      alive = false;
      window.removeEventListener("lexa:settings-updated", onUpdated);
    };
  }, []);

  const ui = useMemo(
    () => ({
      placeholder: branding.inputPlaceholder || "Ask a question...",
      emptyStateText:
        branding.emptyStateText || "Ask me anything about your company!",
    }),
    [branding]
  );

  if (loading) {
    return <div className="p-6">Loading…</div>;
  }

  return (
    <div className="min-h-screen w-full p-4 sm:p-6">
      <div className="max-w-3xl mx-auto">
        <header className="text-center mb-6">
          {/* Only render the logo when a URL is present (prevents baked-in/fallback image) */}
          {branding.logoDataUrl ? (
            <img
              src={branding.logoDataUrl}
              alt=""
              style={{ height: 52 }}
              className="mx-auto mb-2"
            />
          ) : null}

          <h1
            className="mb-1"
            style={{
              fontFamily: "var(--font-family)",
              color: "var(--title-color)",
              fontSize: "var(--title-size)",
              fontWeight: "var(--title-weight)",
              fontStyle: "var(--title-style)",
            }}
          >
            {branding.companyName || "AI Company Chatbot"}
          </h1>

          {branding.taglineText ? (
            <p
              style={{
                fontFamily: "var(--font-family)",
                color: "var(--tagline-color)",
                fontSize: "var(--tagline-size)",
                fontWeight: "var(--tagline-weight)",
                fontStyle: "var(--tagline-style)",
              }}
            >
              {branding.taglineText}
            </p>
          ) : null}
        </header>

        <div className="lexa-glow rounded-2xl p-4 sm:p-6">
          <SimpleChat
            settings={{
              ...branding,
              // ensure SimpleChat sees normalized nulls for bg images
              pageBackgroundUrl: branding.pageBackgroundUrl ?? null,
              chatCardBackgroundUrl: branding.chatCardBackgroundUrl ?? null,
            }}
            ui={ui}
          />
        </div>
      </div>
    </div>
  );
}

