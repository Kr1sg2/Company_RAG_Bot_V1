import type { Branding } from './brandingTypes';
import { normalizeBranding } from './brandingTypes';
import { hexToRgba } from './color';

// Helper functions for safe style conversion
const px = (n?: number | string, defaultValue: number = 0): string => {
  if (typeof n === 'number') return `${n}px`;
  if (typeof n === 'string' && n.trim()) return n;
  return `${defaultValue}px`;
};

const asDim = (v: unknown, defaultValue: string): string => {
  if (typeof v === 'number') return `${v}px`;
  if (typeof v === 'string' && v.trim()) return v;
  return defaultValue;
};

const asPercent = (n?: number, defaultValue: number = 100): string => {
  return `${n ?? defaultValue}%`;
};


export const aiBubbleStyle = (b: Partial<Branding>): React.CSSProperties => {
  const bg = hexToRgba(b.aiBubbleBg ?? '#ffffff', b.aiOpacity ?? 0.9);
  return { backgroundColor: bg, color: b.aiTextColor ?? '#121212' };
};

export const userBubbleStyle = (b: Partial<Branding>): React.CSSProperties => {
  const bg = hexToRgba(b.userBubbleBg ?? '#ffffff', b.userOpacity ?? 0.9);
  return { backgroundColor: bg, color: b.userTextColor ?? '#111111' };
};

export function bubbleContainerStyle(b: Partial<Branding>): React.CSSProperties {
  // Defaults: 8px padding, 70% max width
  const pad = b.bubblePadding ?? 8;
  
  // Handle bubbleMaxWidth as either number or string percentage
  let maxWidth: string;
  if (typeof b.bubbleMaxWidth === 'string') {
    // If it's a string like "60", treat as percentage
    const num = parseInt(b.bubbleMaxWidth, 10);
    if (!isNaN(num)) {
      maxWidth = `${Math.min(100, Math.max(40, num))}%`;
    } else {
      maxWidth = '70%'; // fallback
    }
  } else if (typeof b.bubbleMaxWidth === 'number') {
    maxWidth = `${Math.min(100, Math.max(40, b.bubbleMaxWidth))}%`;
  } else {
    maxWidth = '70%'; // default
  }
  
  return {
    padding: `${pad}px ${Math.round(pad * 1.25)}px`,
    maxWidth,
    borderRadius: b.bubbleRadius ?? '16px',
  };
}

// Shadow presets
const SHADOWS = {
  none: 'none',
  sm: '0 1px 2px rgba(0,0,0,0.08)',
  md: '0 6px 18px rgba(0,0,0,0.12)',
  lg: '0 12px 28px rgba(0,0,0,0.18)',
};

const shadow = (kind: 'none' | 'sm' | 'md' | 'lg'): string => {
  return SHADOWS[kind] || SHADOWS.md;
};

export function avatarClassFromShape(shape?: string) {
  return shape === 'circle' ? 'rounded-full' : shape === 'rounded' ? 'rounded-xl' : 'rounded-none';
}


// Main styling utility class
export class BrandingStyleMapper {
  private branding: Branding;
  
  constructor(branding: Partial<Branding>) {
    this.branding = normalizeBranding(branding);
  }

  // Page-level styles
  getPageStyle(): React.CSSProperties {
    const bgColor = this.branding.pageBackgroundColor || this.branding.background?.color || '#f8fafc';
    const bgUrl = this.branding.pageBackgroundUrl || this.branding.backgroundImageDataUrl;
    const fontFamily = this.branding.fontFamily || 'system-ui, sans-serif';
    
    return {
      background: bgUrl ? `url(${bgUrl}) center/cover no-repeat` : bgColor,
      fontFamily,
      minHeight: '100vh',
    };
  }

  getCardStyle(): React.CSSProperties {
    const b = this.branding;
    const pct = Math.min(100, Math.max(40, b.cardMaxWidthPct ?? 90));
    const w = b.cardWidthPx && b.cardWidthPx > 0 ? b.cardWidthPx : 0;
    const h = b.cardHeightPx && b.cardHeightPx > 0 ? b.cardHeightPx : 0;

    const style: React.CSSProperties = {
      ...(w ? { width: `${w}px` } : { maxWidth: `${pct}%` }),
      borderRadius: b.cardBorderRadius ?? 20,
      transform: `translateY(${b.cardOffsetY ?? 0}px)`,
      // NEW: padding/margins/border/background
      ...(b.cardPadding != null ? { padding: b.cardPadding } : {}),
      ...(b.cardMarginX != null || b.cardMarginY != null
        ? { margin: `${b.cardMarginY ?? 0}px ${b.cardMarginX ?? 0}px` }
        : {}),
      ...(b.cardBorderWidth != null
        ? {
            borderWidth: b.cardBorderWidth,
            borderStyle: 'solid',
            borderColor: b.cardBorderColor ?? '#E2E8F0',
          }
        : {}),
      ...(b.cardBackgroundColor ? { backgroundColor: b.cardBackgroundColor } : {}),
    };

    if (h) {
      Object.assign(style, {
        minHeight: `${h}px`,
        maxHeight: `${h}px`,
        overflowY: 'auto',
      });
    }

    return style;
  }

  getCardWrapperStyle(): React.CSSProperties {
    // Flex container that aligns the card
    const align = this.branding.cardAlign ?? 'center';
    if (align === 'left')  return { display: 'flex', justifyContent: 'flex-start' };
    if (align === 'right') return { display: 'flex', justifyContent: 'flex-end' };
    return { display: 'flex', justifyContent: 'center' }; // center
  }

  // Title styles (company name)
  getTitleStyle(): React.CSSProperties {
    const fontSize = px(this.branding.titleFontSize, 20);
    const bold = this.branding.titleBold ?? true;
    const italic = this.branding.titleItalic ?? false;
    const color = this.branding.titleColor || this.branding.textColor || '#0f172a';

    return {
      fontSize,
      fontWeight: bold ? '600' : 'normal',
      fontStyle: italic ? 'italic' : 'normal',
      color,
      fontFamily: this.branding.fontFamily,
    };
  }

  // Tagline styles
  getTaglineStyle(): React.CSSProperties {
    const fontSize = px(this.branding.taglineFontSize, 14);
    const bold = this.branding.taglineBold ?? false;
    const italic = this.branding.taglineItalic ?? false;
    const color = this.branding.taglineColor || this.branding.mutedTextColor || '#64748b';

    return {
      fontSize,
      fontWeight: bold ? '600' : 'normal',
      fontStyle: italic ? 'italic' : 'normal',
      color,
      fontFamily: this.branding.fontFamily,
    };
  }

  // Chat area styles
  getChatAreaStyle(): React.CSSProperties {
    const height = asDim(this.branding.chatHeight, '60vh');
    const offsetTop = px(this.branding.chatOffsetTop, 16);

    return {
      height,
      paddingTop: offsetTop,
    };
  }

  // Message bubble styles with opacity and border support
  getBubbleStyle(role: 'user' | 'assistant'): React.CSSProperties {
    const maxWidth = asPercent(this.branding.bubbleMaxWidth, 70);
    const radius = this.branding.bubbleRadius || this.branding.bubbles?.radius || '1rem';
    const padding = px(this.branding.bubblePadding, 12);
    const spacing = px(this.branding.messageSpacing, 16);

    let bgColor: string;
    let textColor: string;
    let border: string;
    let fontWeight = 'normal';
    let fontStyle = 'normal';
    let opacity = 1;
    let borderColor: string | undefined;
    let borderWidth: number | undefined;

    if (role === 'user') {
      bgColor = this.branding.userBubbleBg ?? this.branding.bubbles?.userBg ?? '#4f46e5';
      textColor = this.branding.userTextColor ?? '#ffffff';
      border = this.branding.userBubbleBorder ?? 'none';
      fontWeight = this.branding.userBold ? '600' : 'normal';
      fontStyle = this.branding.userItalic ? 'italic' : 'normal';
      opacity = this.branding.userOpacity ?? 1;
      borderColor = this.branding.userBorderColor;
      borderWidth = this.branding.userBorderWidth;
    } else {
      bgColor = this.branding.aiBubbleBg ?? this.branding.bubbles?.aiBg ?? '#f1f5f9';
      textColor = this.branding.aiTextColor ?? this.branding.assistantTextColor ?? '#0f172a';
      border = this.branding.aiBubbleBorder ?? 'none';
      fontWeight = this.branding.assistantBold ? '600' : 'normal';
      fontStyle = this.branding.assistantItalic ? 'italic' : 'normal';
      opacity = this.branding.aiOpacity ?? 1;
      borderColor = this.branding.aiBorderColor;
      borderWidth = this.branding.aiBorderWidth;
    }

    // Apply opacity to background color using RGBA (text stays solid)
    const finalBgColor = hexToRgba(bgColor, opacity);

    // Build border style if border color/width is specified
    let borderStyle: string | undefined;
    if (borderColor && borderWidth && borderWidth > 0) {
      borderStyle = `${borderWidth}px solid ${borderColor}`;
    } else if (border !== 'none') {
      borderStyle = border;
    }

    return {
      maxWidth,
      borderRadius: asDim(radius, '1rem'),
      padding,
      backgroundColor: finalBgColor,
      color: textColor,
      border: borderStyle,
      marginBottom: spacing,
      fontSize: px(this.branding.bodyFontSize, 14),
      fontWeight,
      fontStyle,
      fontFamily: this.branding.fontFamily,
      // Text contrast for readability on transparent backgrounds
      textShadow: opacity < 0.8 ? '0 1px 1px rgba(0,0,0,0.25)' : undefined,
      // Enhance bubble corners
      borderBottomRightRadius: role === 'user' ? '4px' : undefined,
      borderBottomLeftRadius: role === 'assistant' ? '4px' : undefined,
    };
  }

  // Enhanced input field styles
  getInputStyle(): React.CSSProperties {
    const b = this.branding;
    const height = px(b.inputHeight, 48);
    const radius = asDim(b.inputRadius, '12px');
    const fontSize = px(b.inputFontSize, 14);
    const fontWeight = b.inputBold ? '600' : 'normal';
    const fontStyle = b.inputItalic ? 'italic' : 'normal';
    const bgColor = b.inputBackgroundColor || b.inputBg || '#ffffff';
    const textColor = b.inputTextColor || '#111111';
    const primaryColor = b.primaryColor || b.colors?.primary || '#4f46e5';
    
    return {
      backgroundColor: bgColor,
      color: textColor,
      borderRadius: radius,
      borderWidth: px(b.inputBorderWidth, 1),
      borderStyle: 'solid',
      borderColor: b.inputBorderColor || '#d1d5db',
      padding: `${px(b.inputPaddingY, 10)} ${px(b.inputPaddingX, 12)}`,
      height,
      boxShadow: shadow(b.inputShadow || 'sm'),
      fontSize,
      fontWeight,
      fontStyle,
      fontFamily: b.fontFamily,
      '--focus-ring-color': primaryColor,
      '--placeholder-color': b.inputPlaceholderColor || '#9ca3af',
    } as React.CSSProperties & { '--focus-ring-color': string; '--placeholder-color': string };
  }

  // Send button styles
  getButtonStyle(disabled: boolean = false): React.CSSProperties {
    const height = px(this.branding.inputHeight, 48);
    const radius = asDim(this.branding.inputRadius, '0.75rem');
    const bgColor = this.branding.sendButtonBgColor || this.branding.sendBtnBg || this.branding.primaryColor || '#4f46e5';
    const textColor = this.branding.sendButtonTextColor || '#ffffff';
    const accentColor = this.branding.accentColor || this.branding.colors?.accent || '#4338ca';

    return {
      height,
      borderRadius: radius,
      backgroundColor: disabled ? '#94a3b8' : bgColor,
      color: textColor,
      cursor: disabled ? 'not-allowed' : 'pointer',
      fontFamily: this.branding.fontFamily,
      fontSize: px(this.branding.inputFontSize, 14),
      fontWeight: '500',
      '--hover-color': accentColor,
    } as React.CSSProperties & { '--hover-color': string };
  }

  // Avatar styles for both assistant and user
  getAvatarStyle(role: 'user' | 'assistant' = 'assistant'): React.CSSProperties {
    const isUser = role === 'user';
    const size = px(isUser 
      ? this.branding.userAvatarSize || 40 
      : this.branding.avatarSize || this.branding.robotSize || 40
    );
    const shape = isUser 
      ? this.branding.userAvatarShape || 'circle'
      : this.branding.avatarShape || 'circle';
    
    let borderRadius = '0';
    if (shape === 'circle') borderRadius = '50%';
    else if (shape === 'rounded') borderRadius = '0.5rem';

    return {
      width: size,
      height: size,
      borderRadius,
      flexShrink: 0,
      objectFit: 'cover' as const,
    };
  }

  // Check if avatar should be shown
  shouldShowAvatar(role: 'user' | 'assistant', isMobile = false): boolean {
    if (role === 'user') {
      return !!(this.branding.userAvatarImageUrl && 
        (!isMobile || this.branding.showUserAvatarOnMobile !== false));
    } else {
      return !!((this.branding.avatarImageUrl || this.branding.robotIconDataUrl) && 
        (!isMobile || this.branding.showAvatarOnMobile !== false));
    }
  }



  // Empty state text styles
  getEmptyStateStyle(): React.CSSProperties {
    const fontSize = px(this.branding.bodyFontSize, 14);
    const color = this.branding.mutedTextColor || '#64748b';

    return {
      fontSize,
      color,
      fontFamily: this.branding.fontFamily,
      textAlign: 'center' as const,
    };
  }

  // Input placeholder styles (for custom placeholder handling)
  getPlaceholderStyle(): React.CSSProperties {
    const fontSize = px(this.branding.inputFontSize, 14);
    const color = this.branding.mutedTextColor || '#9ca3af';

    return {
      fontSize,
      color,
      fontFamily: this.branding.fontFamily,
    };
  }

  // Source links styles
  getSourceLinkStyle(): React.CSSProperties {
    const color = this.branding.primaryColor || this.branding.colors?.primary || '#4f46e5';
    
    return {
      color,
      textDecoration: 'underline',
      fontSize: 'inherit',
      fontFamily: this.branding.fontFamily,
    };
  }

  // Loading indicator styles
  getLoadingStyle(): React.CSSProperties {
    const color = this.branding.mutedTextColor || '#64748b';
    
    return {
      color,
      fontSize: px(this.branding.bodyFontSize, 14),
      fontFamily: this.branding.fontFamily,
    };
  }

  // Get send button text
  getSendButtonText(): string {
    return this.branding.sendBtnText || 'Send';
  }

  // Get avatar image URL for specific role or fallback
  getAvatarImageUrl(role?: 'user' | 'assistant'): string | undefined {
    if (role === 'user') {
      return this.branding.userAvatarImageUrl;
    } else if (role === 'assistant') {
      return this.branding.avatarImageUrl || this.branding.robotIconDataUrl || undefined;
    } else {
      // Fallback for legacy usage without role
      return this.branding.avatarImageUrl || 
             this.branding.robotIconDataUrl || 
             this.branding.robotLogoDataUrl ||
             this.branding.robot?.imageUrl || undefined;
    }
  }

  // Get avatar position for specific role or default
  getAvatarPosition(role?: 'user' | 'assistant'): 'left' | 'right' | 'none' {
    if (role === 'user') {
      return this.branding.userAvatarPosition || 'right';
    } else if (role === 'assistant') {
      return this.branding.avatarPosition === 'right' ? 'right' : 'left';
    } else {
      // Default without role
      return this.branding.avatarPosition || 'left';
    }
  }




}

// Convenience functions for direct use
export function createStyleMapper(branding: Partial<Branding>): BrandingStyleMapper {
  return new BrandingStyleMapper(branding);
}

export function getPageStyles(branding: Partial<Branding>): React.CSSProperties {
  return new BrandingStyleMapper(branding).getPageStyle();
}

export function getCardStyles(branding: Partial<Branding>): React.CSSProperties {
  return new BrandingStyleMapper(branding).getCardStyle();
}

export function getBubbleStyles(branding: Partial<Branding>, role: 'user' | 'assistant'): React.CSSProperties {
  return new BrandingStyleMapper(branding).getBubbleStyle(role);
}

export function getTitleStyles(branding: Partial<Branding>): React.CSSProperties {
  return new BrandingStyleMapper(branding).getTitleStyle();
}

export function getTaglineStyles(branding: Partial<Branding>): React.CSSProperties {
  return new BrandingStyleMapper(branding).getTaglineStyle();
}

export function getCardStyle(b: Partial<Branding>): React.CSSProperties {
  const pct = Math.min(100, Math.max(40, b.cardMaxWidthPct ?? 90));
  const w = b.cardWidthPx && b.cardWidthPx > 0 ? b.cardWidthPx : 0;
  const h = b.cardHeightPx && b.cardHeightPx > 0 ? b.cardHeightPx : 0;

  const style: React.CSSProperties = {
    ...(w ? { width: `${w}px` } : { maxWidth: `${pct}%` }),
    borderRadius: b.cardBorderRadius ?? 20,
    transform: `translateY(${b.cardOffsetY ?? 0}px)`,
    // NEW: padding/margins/border/background
    ...(b.cardPadding != null ? { padding: b.cardPadding } : {}),
    ...(b.cardMarginX != null || b.cardMarginY != null
      ? { margin: `${b.cardMarginY ?? 0}px ${b.cardMarginX ?? 0}px` }
      : {}),
    ...(b.cardBorderWidth != null
      ? {
          borderWidth: b.cardBorderWidth,
          borderStyle: 'solid',
          borderColor: b.cardBorderColor ?? '#E2E8F0',
        }
      : {}),
    ...(b.cardBackgroundColor ? { backgroundColor: b.cardBackgroundColor } : {}),
  };

  if (h) {
    Object.assign(style, {
      minHeight: `${h}px`,
      maxHeight: `${h}px`,
      overflowY: 'auto',
    });
  }

  return style;
}

export function getCardWrapperStyle(b: Partial<Branding>): React.CSSProperties {
  // Flex container that aligns the card
  const align = b.cardAlign ?? 'center';
  if (align === 'left')  return { display: 'flex', justifyContent: 'flex-start' };
  if (align === 'right') return { display: 'flex', justifyContent: 'flex-end' };
  return { display: 'flex', justifyContent: 'center' }; // center
}

