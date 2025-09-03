// Complete Branding interface matching settings.json schema
export type ResponseStyle = 'auto' | 'paragraphs' | 'sentences' | 'bullets' | 'numbers';
export type ResponseFormat = 'paragraphs' | 'bulletPoints' | 'letSystemChoose';

export interface Branding {
  // Basic Company Info
  companyName?: string;
  taglineText?: string;
  emptyStateText?: string;
  inputPlaceholder?: string;
  logoDataUrl?: string | null;
  companyLogoDataUrl?: string | null;
  faviconUrl?: string | null;
  
  // Typography - Title
  titleFontSize?: number;
  titleBold?: boolean;
  titleItalic?: boolean;
  titleColor?: string;
  
  // Typography - Tagline
  taglineFontSize?: number;
  taglineBold?: boolean;
  taglineItalic?: boolean;
  taglineColor?: string;
  
  // Typography - General
  fontFamily?: string;
  bodyFontSize?: number;
  inputFontSize?: number;
  inputBold?: boolean;
  inputItalic?: boolean;
  
  // Colors - Theme
  colors?: {
    primary?: string;
    accent?: string;
    bg?: string;
    text?: string;
  };
  primaryColor?: string;
  accentColor?: string;
  textColor?: string;
  mutedTextColor?: string;
  foregroundColor?: string;
  mutedForegroundColor?: string;
  
  // Chat Bubbles - Structure
  bubbles?: {
    radius?: string;
    aiBg?: string;
    userBg?: string;
  };
  bubbleRadius?: string;
  bubblePadding?: number;
  bubbleMaxWidth?: number;
  
  // Chat Bubbles - AI Styling
  aiBubbleBg?: string;
  aiTextColor?: string;
  aiBubbleBorder?: string;
  assistantTextColor?: string;
  assistantBold?: boolean;
  assistantItalic?: boolean;
  aiOpacity?: number; // 0.0-1.0
  aiBorderColor?: string;
  aiBorderWidth?: number;
  
  // Chat Bubbles - User Styling
  userBubbleBg?: string;
  userTextColor?: string;
  userBubbleBorder?: string;
  userBold?: boolean;
  userItalic?: boolean;
  userOpacity?: number; // 0.0-1.0
  userBorderColor?: string;
  userBorderWidth?: number;

  // Chat Bubbles - Show/Hide and Shape Control
  showBubbles?: boolean;        // default true
  bubbleRadiusPx?: number;      // optional per-branding
  bubblePaddingX?: number;      // optional per-branding
  bubblePaddingY?: number;      // optional per-branding
  
  // Card/Layout - Extended Dimensions & Controls
  chatWidth?: string | number;
  chatHeight?: string | number;
  cardRadius?: string | number;
  cardPadding?: number;       // px (inside the card) 
  cardMarginX?: number;       // px (outer horizontal)
  cardMarginY?: number;       // px (outer vertical)
  cardBorderWidth?: number;   // px
  cardBorderColor?: string;
  cardShadow?: 'none'|'sm'|'md'|'lg';
  cardAlign?: 'center'|'left'|'right';
  cardOffsetY?: number;       // px offset up/down
  
  // Input & Card new styling controls
  inputBorderRadius?: number;   // px, default 12
  inputPaddingX?: number;       // px, default 12
  inputPaddingY?: number;       // px, default 10
  inputBorderWidth?: number;    // px, default 1
  inputBorderColor?: string;    // hex, default '#D1D5DB'
  
  // Card (panel)
  cardBorderRadius?: number;    // px, default 20
  cardMaxWidthPct?: number;     // 40..100, default 90
  
  // NEW: explicit size overrides
  cardWidthPx?: number;         // if >0, overrides cardMaxWidthPct
  cardHeightPx?: number;        // if >0, fixed height with internal scroll
  
  inputHeight?: number;
  inputRadius?: string | number;
  messageSpacing?: number;
  chatOffsetTop?: string | number;
  
  // Backgrounds - Page
  pageBackgroundColor?: string;
  pageBackgroundUrl?: string | null;
  backgroundImageDataUrl?: string | null;
  background?: {
    color?: string;
    imageUrl?: string;
  };
  
  // Backgrounds - Card
  cardBackgroundColor?: string;
  cardBackgroundUrl?: string | null;
  chatCardBackgroundColor?: string;
  chatCardBackgroundUrl?: string | null;
  cardBackgroundCssOverride?: string;
  cardBg?: string;
  cardOpacity?: number;
  
  // Input Styling - Extended
  inputBackgroundColor?: string;
  inputBg?: string;
  inputTextColor?: string;
  inputPlaceholderColor?: string;
  inputShadow?: 'none'|'sm'|'md'|'lg';
  
  // Button Styling
  sendButtonBgColor?: string;
  sendBtnBg?: string;
  sendButtonTextColor?: string;
  sendBtnText?: string;
  
  // Shadows & Effects
  enableShadow?: boolean;
  shadowColor?: string;
  shadowBlur?: number;
  shadowSpread?: number;
  shadowOpacity?: number;
  enableGlow?: boolean;
  glowColor?: string;
  glowBlur?: number;
  glowSpread?: number;
  glowOpacity?: number;
  shadow?: {
    color?: string;
    blur?: number;
    spread?: number;
    opacity?: number;
  };
  
  // Robot/Avatar - Assistant
  avatarImageUrl?: string | null;
  robotIconDataUrl?: string | null;
  robotLogoDataUrl?: string | null;
  avatarSize?: number;
  robotSize?: number;
  avatarPosition?: 'left' | 'right' | 'none';
  avatarShape?: 'circle' | 'rounded' | 'square';
  showAvatarOnMobile?: boolean;
  robot?: {
    imageUrl?: string;
    size?: number;
  };
  
  // User Avatar
  userAvatarImageUrl?: string;
  userAvatarSize?: number;
  userAvatarPosition?: 'left' | 'right';
  userAvatarShape?: 'circle' | 'square' | 'rounded';
  showUserAvatarOnMobile?: boolean;
  
  // Audio / Speech - TTS
  enableTextToSpeech?: boolean;
  ttsVoice?: string;
  voice?: string;
  ttsSpeed?: number;
  ttsAutoPlay?: boolean;
  
  // Audio / Speech - STT
  enableSpeechToText?: boolean;
  sttEnabled?: boolean;
  sttLanguage?: string;
  sttAutoSend?: boolean;
  
  // UI Controls
  showAudioControls?: boolean;
  
  // LLM Controls
  aiModel?: string;
  model?: string;                  // e.g. "gpt-4o-mini" (default from backend if absent)
  aiTemperature?: number;
  temperature?: number;            // 0..2
  aiMaxTokens?: number;
  max_tokens?: number;             // 1..4000 (or backend clamp)
  aiTopK?: number;
  top_k?: number;
  top_p?: number;                  // 0..1
  frequency_penalty?: number;      // -2..2
  presence_penalty?: number;       // -2..2
  aiStrictness?: 'creative' | 'balanced' | 'precise' | 'custom';
  strictness?: number;             // 0..10 (if present, backend may fold into system prompt)
  aiSystemPrompt?: string;
  systemPrompt?: string;           // optional custom system prompt text
  aiStreamResponses?: boolean;
  aiRetainContext?: boolean;
  aiResponseStyle?: ResponseStyle;
  responseFormat?: ResponseFormat;
  
  // Theme & Misc
  themeMode?: 'light' | 'dark' | 'system';
  fontSize?: number;
  title?: string;
  uiHeader?: string;
  uiSubtitle?: string;
  uiPlaceholder?: string;
  
  // Legacy nested objects
  foreground?: {
    color?: string;
  };
  tagline?: {
    fontFamily?: string;
    fontSize?: number;
    color?: string;
  };
  emptyState?: {
    fontFamily?: string;
    fontSize?: number;
    color?: string;
  };
  placeholder?: {
    fontFamily?: string;
    fontSize?: number;
    color?: string;
  };
  branding?: any; // Legacy nested branding object
}

// Default branding values with all possible fields
export const DEFAULT_BRANDING: Branding = {
  // Basic
  companyName: 'Company Chat',
  taglineText: 'Ask questions about your company documents.',
  emptyStateText: 'Start by asking something like "What is the company dress code?"',
  inputPlaceholder: 'Type your question and press Enter…',
  logoDataUrl: null,
  faviconUrl: null,
  
  // Typography - Title
  titleFontSize: 20,
  titleBold: true,
  titleItalic: false,
  titleColor: '#0f172a',
  
  // Typography - Tagline
  taglineFontSize: 14,
  taglineBold: false,
  taglineItalic: false,
  taglineColor: '#64748b',
  
  // Typography - General
  fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  bodyFontSize: 14,
  inputFontSize: 14,
  inputBold: false,
  inputItalic: false,
  
  // Colors
  colors: {
    primary: '#4f46e5',
    accent: '#4338ca',
    bg: '#f8fafc',
    text: '#0f172a',
  },
  primaryColor: '#4f46e5',
  accentColor: '#4338ca',
  textColor: '#0f172a',
  mutedTextColor: '#64748b',
  
  // Chat Bubbles
  bubbles: {
    radius: '1rem',
    aiBg: '#f1f5f9',
    userBg: '#4f46e5',
  },
  bubblePadding: 12,
  bubbleMaxWidth: 70,
  aiBubbleBg: '#f1f5f9',
  aiTextColor: '#0f172a',
  aiBubbleBorder: 'none',
  userBubbleBg: '#4f46e5',
  userTextColor: '#ffffff',
  userBubbleBorder: 'none',
  showBubbles: true,
  
  // Card/Layout - Extended
  chatWidth: '64rem',
  chatHeight: '60vh',
  cardRadius: '1rem',
  cardPadding: 16,
  cardMarginX: 0,
  cardMarginY: 16,
  cardBorderWidth: 0,
  cardBorderColor: '',
  cardShadow: 'md' as const,
  cardAlign: 'center' as const,
  cardOffsetY: 0,
  
  // Input & Card styling controls
  inputBorderRadius: 12,
  cardBorderRadius: 20,
  cardMaxWidthPct: 90,
  cardWidthPx: 0,    // 0 means use cardMaxWidthPct instead
  cardHeightPx: 0,   // 0 means auto height
  
  messageSpacing: 16,
  inputHeight: 48,
  inputRadius: '0.75rem',
  chatOffsetTop: 16,
  
  // Backgrounds
  pageBackgroundColor: '#f8fafc',
  pageBackgroundUrl: null,
  cardBackgroundColor: 'rgba(255,255,255,0.9)',
  cardBg: 'rgba(255,255,255,0.9)',
  cardOpacity: 90,
  
  // Input/Button - Extended
  inputBackgroundColor: '#ffffff',
  inputTextColor: '#0f172a',
  inputPaddingX: 12,
  inputPaddingY: 10,
  inputBorderWidth: 1,
  inputBorderColor: '#d1d5db',
  inputPlaceholderColor: '#9ca3af',
  inputShadow: 'sm' as const,
  sendButtonBgColor: '#4f46e5',
  sendButtonTextColor: '#ffffff',
  sendBtnText: 'Send',
  
  // Shadows
  enableShadow: true,
  shadowColor: '#000000',
  shadowBlur: 10,
  shadowSpread: 0,
  shadowOpacity: 20,
  enableGlow: false,
  
  // Avatar
  avatarImageUrl: null,
  avatarSize: 40,
  avatarPosition: 'left',
  avatarShape: 'circle',
  showAvatarOnMobile: true,
  
  // Audio
  enableTextToSpeech: false,
  enableSpeechToText: false,
  ttsVoice: 'default',
  ttsSpeed: 1,
  ttsAutoPlay: false,
  sttLanguage: 'en-US',
  sttAutoSend: false,
  showAudioControls: true,
  
  // LLM
  aiModel: 'gpt-4',
  aiTemperature: 0.7,
  aiMaxTokens: 2048,
  aiTopK: 50,
  aiStrictness: 'balanced',
  aiSystemPrompt: 'You are a helpful AI assistant.',
  aiStreamResponses: true,
  aiRetainContext: true,
  aiResponseStyle: 'auto',
  responseFormat: 'paragraphs',
  
  // Theme
  themeMode: 'system',
};

// Helper to get branding value with multiple fallback keys
export function getBrandingValue<T>(
  branding: Partial<Branding> | null | undefined,
  ...keys: (keyof Branding)[]
): T | undefined {
  if (!branding) return undefined;
  
  for (const key of keys) {
    const value = branding[key];
    if (value !== undefined && value !== null) {
      return value as T;
    }
  }
  return undefined;
}

// Helper to get branding value with fallback to default
export function getBrandingValueWithDefault<K extends keyof Branding>(
  branding: Partial<Branding> | null | undefined,
  key: K,
  fallback?: Branding[K]
): NonNullable<Branding[K]> {
  const value = branding?.[key] ?? fallback ?? DEFAULT_BRANDING[key];
  return value as NonNullable<Branding[K]>;
}

// Helper to normalize branding object from various schemas
export function normalizeBranding(raw: any): Branding {
  if (!raw) return DEFAULT_BRANDING;
  
  const normalized: Branding = { ...raw };
  
  // Handle legacy nested objects
  if (raw.colors) {
    normalized.primaryColor = raw.colors.primary || normalized.primaryColor;
    normalized.accentColor = raw.colors.accent || normalized.accentColor;
  }
  
  if (raw.bubbles) {
    normalized.bubbleRadius = raw.bubbles.radius || normalized.bubbleRadius;
    normalized.aiBubbleBg = raw.bubbles.aiBg || normalized.aiBubbleBg;
    normalized.userBubbleBg = raw.bubbles.userBg || normalized.userBubbleBg;
  }
  
  if (raw.background) {
    normalized.pageBackgroundColor = raw.background.color || normalized.pageBackgroundColor;
    normalized.pageBackgroundUrl = raw.background.imageUrl || normalized.pageBackgroundUrl;
  }
  
  if (raw.shadow) {
    normalized.shadowColor = raw.shadow.color || normalized.shadowColor;
    normalized.shadowBlur = raw.shadow.blur || normalized.shadowBlur;
    normalized.shadowSpread = raw.shadow.spread || normalized.shadowSpread;
    normalized.shadowOpacity = (raw.shadow.opacity || 0) * 100; // Convert to percentage
  }
  
  if (raw.robot) {
    normalized.avatarImageUrl = raw.robot.imageUrl || normalized.avatarImageUrl;
    normalized.avatarSize = raw.robot.size || normalized.avatarSize;
  }
  
  // Handle alternative field names
  normalized.companyName = raw.companyName || raw.title || normalized.companyName;
  normalized.taglineText = raw.taglineText || raw.uiHeader || normalized.taglineText;
  normalized.emptyStateText = raw.emptyStateText || raw.uiSubtitle || normalized.emptyStateText;
  normalized.inputPlaceholder = raw.inputPlaceholder || raw.uiPlaceholder || normalized.inputPlaceholder;
  
  // LLM field mapping
  normalized.aiModel = raw.aiModel || raw.model || normalized.aiModel;
  normalized.aiTemperature = raw.aiTemperature || raw.temperature || normalized.aiTemperature;
  normalized.aiMaxTokens = raw.aiMaxTokens || raw.max_tokens || normalized.aiMaxTokens;
  normalized.aiTopK = raw.aiTopK || raw.top_k || normalized.aiTopK;
  
  // TTS field mapping
  normalized.ttsVoice = raw.ttsVoice || raw.voice || normalized.ttsVoice;
  normalized.enableSpeechToText = raw.enableSpeechToText || raw.sttEnabled || normalized.enableSpeechToText;
  
  return normalized;
}