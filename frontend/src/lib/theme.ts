/* src/lib/theme.ts */
import type { Branding } from "./brandingTypes";

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

// Accept either 0..1 or 0..100 and return 0..1
function normalizeAlpha(x: number | undefined, fallback = 1) {
  if (typeof x !== "number" || isNaN(x)) return fallback;
  // If > 1, assume percent; if 0..1, assume fraction
  return x > 1 ? clamp(x, 0, 100) / 100 : clamp(x, 0, 1);
}

function hexToRgb(hex: string) {
  const h = (hex || "").trim().replace(/^#/, "");
  const p = (s: string) => parseInt(s, 16);
  if (h.length === 3) {
    return { r: p(h[0]+h[0]), g: p(h[1]+h[1]), b: p(h[2]+h[2]) };
  }
  return { r: p(h.slice(0,2)), g: p(h.slice(2,4)), b: p(h.slice(4,6)) };
}

// Replace existing rgba helper (or update it) to use normalizeAlpha
function rgbaFromHex(hex: string, alphaMixed: number | undefined, fallbackAlpha = 1) {
  const a = normalizeAlpha(alphaMixed, fallbackAlpha);
  const { r, g, b } = hexToRgb(hex || "#ffffff");
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

export function applyBrandingVars(b: Partial<Branding> = {}) {
  const root = document.documentElement;

  const set = (name: string, value: string | number | undefined) => {
    if (value === undefined || value === null) return;
    root.style.setProperty(name, String(value));
  };

  // base colors
  if (b.aiBubbleBg) set("--ai-bubble-bg", b.aiBubbleBg);
  if (b.aiTextColor) set("--ai-text-color", b.aiTextColor);
  if (b.userBubbleBg) set("--user-bubble-bg", b.userBubbleBg);
  if (b.userTextColor) set("--user-text-color", b.userTextColor);
  if (b.cardBackgroundColor) set("--card-bg", b.cardBackgroundColor);

  // layout
  if (typeof b.cardWidthPx === "number" && b.cardWidthPx > 0) {
    set("--card-width-pct", "100");
    set("--card-max-width-pct", "100");
    root.style.setProperty("--card-fixed-width", `${b.cardWidthPx}px`);
  } else {
    if (typeof b.cardMaxWidthPct === "number") set("--card-max-width-pct", clamp(b.cardMaxWidthPct, 0, 100));
    root.style.removeProperty("--card-fixed-width");
  }
  if (typeof b.chatOffsetTop === "number") set("--card-offset-top-px", b.chatOffsetTop);
  if (typeof b.cardBorderRadius === "number") set("--card-border-radius-px", b.cardBorderRadius);
  if (typeof b.cardRadius === "string") {
    const numericValue = parseInt(b.cardRadius, 10);
    if (!isNaN(numericValue)) set("--card-border-radius-px", numericValue);
  }

  // compute RGBA backgrounds so text remains solid
  const computed = getComputedStyle(root);

  // CARD
  const cardHex =
    b.cardBackgroundColor ||
    computed.getPropertyValue("--card-bg").trim() ||
    "#ffffff";

  const cardAlphaRaw =
    (b as any).cardOpacityPct ??
    (typeof b.cardOpacity === "number" ? b.cardOpacity : undefined);

  set("--card-bg-rgba", rgbaFromHex(cardHex, cardAlphaRaw, 1));

  // AI BUBBLE
  const aiHex =
    b.aiBubbleBg ||
    computed.getPropertyValue("--ai-bubble-bg").trim() ||
    "#d946ef";

  const aiAlphaRaw =
    (b as any).aiBubbleOpacityPct ??
    (b as any).aiOpacityPct ??
    (typeof b.aiOpacity === "number" ? b.aiOpacity : undefined);

  set("--ai-bubble-bg-rgba", rgbaFromHex(aiHex, aiAlphaRaw, 1));

  // USER BUBBLE
  const userHex =
    b.userBubbleBg ||
    computed.getPropertyValue("--user-bubble-bg").trim() ||
    "#50c8e8";

  const userAlphaRaw =
    (b as any).userBubbleOpacityPct ??
    (b as any).userOpacityPct ??
    (typeof b.userOpacity === "number" ? b.userOpacity : undefined);

  set("--user-bubble-bg-rgba", rgbaFromHex(userHex, userAlphaRaw, 1));

  // shape defaults (let CSS defaults stand unless overridden)
  if (typeof b.bubbleRadiusPx === "number") root.style.setProperty("--bubble-radius-px", String(b.bubbleRadiusPx));
  if (typeof b.bubblePaddingX === "number") root.style.setProperty("--bubble-pad-x", String(b.bubblePaddingX));
  if (typeof b.bubblePaddingY === "number") root.style.setProperty("--bubble-pad-y", String(b.bubblePaddingY));

  // Global bubble toggle (keep this block, ensure behavior matches)
  if (b.showBubbles === false) {
    root.style.setProperty("--ai-bubble-bg-rgba", "transparent");
    root.style.setProperty("--user-bubble-bg-rgba", "transparent");
    root.style.setProperty("--bubble-radius-px", "0");
    root.style.setProperty("--bubble-pad-x", "0");
    root.style.setProperty("--bubble-pad-y", "0");
  }
  // if true or undefined → do nothing; computed RGBA values above apply
}