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
  
  // Fonts - Typography
  fontFamily?: string;
  titleFontSize?: number;
  bodyFontSize?: number;
  titleBold?: boolean;
  titleItalic?: boolean;
  taglineFontSize?: number;
  taglineBold?: boolean;
  taglineItalic?: boolean;
  
  // Enhanced Bubble Controls
  bubblePadding?: number;
  bubbleMaxWidth?: number;
  aiTextColor?: string;
  aiBubbleBorder?: string;
  userTextColor?: string;
  userBubbleBorder?: string;
  
  // Enhanced Card Controls
  cardPadding?: number;
  inputHeight?: number;
  inputRadius?: number;
  messageSpacing?: number;
  
  // Backgrounds & Shadows
  pageBackgroundColor?: string;
  cardBackgroundColor?: string;
  cardOpacity?: number;
  shadowColor?: string;
  shadowBlur?: number;
  shadowSpread?: number;
  shadowOpacity?: number;
  enableShadow?: boolean;
  enableGlow?: boolean;
  
  // Robot / Avatar
  avatarImageUrl?: string | null;
  avatarSize?: number;
  avatarPosition?: string;
  avatarShape?: string;
  showAvatarOnMobile?: boolean;
  
  // Audio / TTS & STT
  enableTextToSpeech?: boolean;
  enableSpeechToText?: boolean;
  ttsVoice?: string;
  ttsSpeed?: number;
  sttLanguage?: string;
  sttAutoSend?: boolean;
  showAudioControls?: boolean;
  ttsAutoPlay?: boolean;
  
  // LLM Controls
  aiModel?: string;
  aiTemperature?: number;
  aiMaxTokens?: number;
  aiTopK?: number;
  aiStrictness?: string;
  aiSystemPrompt?: string;
  aiStreamResponses?: boolean;
  aiRetainContext?: boolean;
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