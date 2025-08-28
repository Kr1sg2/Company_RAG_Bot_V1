// Complete Branding interface with all 55+ controls
export interface Branding {
  // Basic
  companyName?: string;
  taglineText?: string;
  emptyStateText?: string;
  inputPlaceholder?: string;
  logoDataUrl?: string | null;
  faviconUrl?: string | null;
  
  // Typography
  fontFamily?: string;
  titleFontSize?: number;
  titleBold?: boolean;
  titleItalic?: boolean;
  bodyFontSize?: number;
  taglineFontSize?: number;
  taglineBold?: boolean;
  taglineItalic?: boolean;
  
  // Colors
  colors?: {
    primary?: string;
    accent?: string;
    bg?: string;
    text?: string;
  };
  textColor?: string; // Backward compatibility
  mutedTextColor?: string;
  
  // Chat Bubbles
  bubbles?: {
    radius?: string;
    aiBg?: string;
    userBg?: string;
  };
  bubbleRadius?: string; // Alternative naming
  bubblePadding?: number;
  bubbleMaxWidth?: number;
  aiBubbleBg?: string; // Alternative naming
  aiTextColor?: string;
  aiBubbleBorder?: string;
  userBubbleBg?: string; // Alternative naming
  userTextColor?: string;
  userBubbleBorder?: string;
  
  // Card/Layout
  chatWidth?: string | number;
  chatHeight?: string | number;
  cardRadius?: string | number;
  cardPadding?: number;
  messageSpacing?: number;
  inputHeight?: number;
  inputRadius?: string | number;
  chatOffsetTop?: string | number;
  
  // Backgrounds/Shadow
  pageBackgroundColor?: string;
  pageBackgroundUrl?: string | null;
  cardBackgroundColor?: string;
  cardBackgroundUrl?: string | null;
  cardBackgroundCssOverride?: string;
  cardBg?: string; // Backward compatibility
  cardOpacity?: number;
  enableShadow?: boolean;
  shadowColor?: string;
  shadowBlur?: number;
  shadowSpread?: number;
  shadowOpacity?: number;
  enableGlow?: boolean;
  
  // Robot/Avatar
  avatarImageUrl?: string | null;
  avatarSize?: number;
  avatarPosition?: 'left' | 'right' | 'none';
  avatarShape?: 'circle' | 'rounded' | 'square';
  showAvatarOnMobile?: boolean;
  
  // Audio / Speech
  // TTS
  enableTextToSpeech?: boolean;
  ttsVoice?: string;
  ttsSpeed?: number;
  ttsAutoPlay?: boolean;
  
  // STT
  enableSpeechToText?: boolean;
  sttLanguage?: string;
  sttAutoSend?: boolean;
  
  // UI toggles
  showAudioControls?: boolean;
  
  // LLM Controls
  aiModel?: string;
  aiTemperature?: number;
  aiMaxTokens?: number;
  aiTopK?: number;
  aiStrictness?: 'creative' | 'balanced' | 'precise';
  aiSystemPrompt?: string;
  aiStreamResponses?: boolean;
  aiRetainContext?: boolean;
}

// Default branding values
export const DEFAULT_BRANDING: Required<Branding> = {
  // Basic
  companyName: 'Company Chat',
  taglineText: 'Ask questions about your company documents.',
  emptyStateText: 'Start by asking something like "What is the company dress code?"',
  inputPlaceholder: 'Type your question and press Enter…',
  logoDataUrl: null,
  faviconUrl: null,
  
  // Typography
  fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  titleFontSize: 20,
  titleBold: true,
  titleItalic: false,
  bodyFontSize: 14,
  taglineFontSize: 14,
  taglineBold: false,
  taglineItalic: false,
  
  // Colors
  colors: {
    primary: '#4f46e5',
    accent: '#4338ca',
    bg: '#f8fafc',
    text: '#0f172a',
  },
  textColor: '#0f172a',
  mutedTextColor: '#64748b',
  
  // Chat Bubbles
  bubbles: {
    radius: '1rem',
    aiBg: '#f1f5f9',
    userBg: '#4f46e5',
  },
  bubbleRadius: '1rem',
  bubblePadding: 12,
  bubbleMaxWidth: 70,
  aiBubbleBg: '#f1f5f9',
  aiTextColor: '#0f172a',
  aiBubbleBorder: 'none',
  userBubbleBg: '#4f46e5',
  userTextColor: '#ffffff',
  userBubbleBorder: 'none',
  
  // Card/Layout
  chatWidth: '64rem',
  chatHeight: '60vh',
  cardRadius: '1rem',
  cardPadding: 0,
  messageSpacing: 16,
  inputHeight: 48,
  inputRadius: '0.75rem',
  chatOffsetTop: 16,
  
  // Backgrounds/Shadow
  pageBackgroundColor: '#f8fafc',
  pageBackgroundUrl: null,
  cardBackgroundColor: 'rgba(255,255,255,0.9)',
  cardBackgroundUrl: null,
  cardBackgroundCssOverride: '',
  cardBg: 'rgba(255,255,255,0.9)',
  cardOpacity: 90,
  enableShadow: true,
  shadowColor: '#000000',
  shadowBlur: 10,
  shadowSpread: 0,
  shadowOpacity: 20,
  enableGlow: false,
  
  // Robot/Avatar
  avatarImageUrl: null,
  avatarSize: 40,
  avatarPosition: 'left',
  avatarShape: 'circle',
  showAvatarOnMobile: true,
  
  // Audio / Speech
  // TTS
  enableTextToSpeech: false,
  ttsVoice: 'default',
  ttsSpeed: 1,
  ttsAutoPlay: false,
  
  // STT
  enableSpeechToText: false,
  sttLanguage: 'en-US',
  sttAutoSend: false,
  
  // UI toggles
  showAudioControls: true,
  
  // LLM Controls
  aiModel: 'gpt-4',
  aiTemperature: 0.7,
  aiMaxTokens: 2048,
  aiTopK: 50,
  aiStrictness: 'balanced',
  aiSystemPrompt: 'You are a helpful AI assistant.',
  aiStreamResponses: true,
  aiRetainContext: true,
};

// Helper to get branding value with fallback to default
export function getBrandingValue<K extends keyof Branding>(
  branding: Partial<Branding> | null | undefined,
  key: K,
  fallback?: Branding[K]
): NonNullable<Branding[K]> {
  const value = branding?.[key] ?? fallback ?? DEFAULT_BRANDING[key];
  return value as NonNullable<Branding[K]>;
}