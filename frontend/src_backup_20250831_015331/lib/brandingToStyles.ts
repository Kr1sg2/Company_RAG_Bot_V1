import type { Branding } from './brandingTypes';
import { getBrandingValue, normalizeBranding } from './brandingTypes';
import { hexToRgba as hexToRgbaUtil } from './color';

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

const asOpacity = (n?: number, defaultValue: number = 1): number => {
  if (n === undefined) return defaultValue;
  return Math.max(0, Math.min(1, n / 100));
};

const hexToRgba = hexToRgbaUtil;


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

  // Chat card container styles
  getCardStyle(): React.CSSProperties {
    const width = asDim(this.branding.chatWidth, '64rem');
    const radius = asDim(this.branding.cardRadius, '1rem');
    const padding = px(this.branding.cardPadding, 0);
    const opacity = asOpacity(this.branding.cardOpacity, 90);
    
    // Handle multiple background color field names
    let bgColor = getBrandingValue<string>(
      this.branding, 
      'cardBackgroundColor', 
      'chatCardBackgroundColor', 
      'cardBg'
    ) || 'rgba(255,255,255,0.9)';
    
    const bgUrl = getBrandingValue<string>(this.branding, 'cardBackgroundUrl', 'chatCardBackgroundUrl');
    const cssOverride = this.branding.cardBackgroundCssOverride;
    
    // Apply opacity if it's different from default
    if (this.branding.cardOpacity !== undefined && this.branding.cardOpacity !== 90) {
      bgColor = hexToRgba(bgColor.replace('#', '') ? bgColor : '#ffffff', opacity);
    }
    
    // Shadow configuration
    const enableShadow = this.branding.enableShadow ?? true;
    const shadowColor = this.branding.shadowColor || '#000000';
    const shadowBlur = this.branding.shadowBlur || 10;
    const shadowSpread = this.branding.shadowSpread || 0;
    const shadowOpacity = asOpacity(this.branding.shadowOpacity, 20);
    const enableGlow = this.branding.enableGlow || false;
    
    let boxShadow = 'none';
    if (enableShadow) {
      const shadowRgba = hexToRgba(shadowColor, shadowOpacity);
      boxShadow = `0 ${px(shadowSpread, 0)} ${px(shadowBlur, 10)} ${shadowRgba}`;
    }
    
    if (enableGlow) {
      const glowColor = this.branding.glowColor || this.branding.primaryColor || '#4f46e5';
      const glowBlur = this.branding.glowBlur || 20;
      const glowOpacity = asOpacity(this.branding.glowOpacity, 30);
      const glowShadow = `0 0 ${px(glowBlur)} ${hexToRgba(glowColor, glowOpacity)}`;
      
      boxShadow = boxShadow === 'none' ? glowShadow : `${boxShadow}, ${glowShadow}`;
    }

    return {
      maxWidth: width,
      borderRadius: radius,
      backgroundColor: bgUrl ? 'transparent' : bgColor,
      backgroundImage: bgUrl ? `url(${bgUrl})` : cssOverride ? undefined : undefined,
      background: cssOverride || undefined,
      backgroundSize: bgUrl ? 'cover' : undefined,
      backgroundPosition: bgUrl ? 'center' : undefined,
      border: '1px solid rgba(226, 232, 240, 0.5)',
      backdropFilter: 'blur(8px)',
      padding,
      boxShadow,
    };
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
      bgColor = this.branding.userBubbleBg || this.branding.bubbles?.userBg || '#4f46e5';
      textColor = this.branding.userTextColor || '#ffffff';
      border = this.branding.userBubbleBorder || 'none';
      fontWeight = this.branding.userBold ? '600' : 'normal';
      fontStyle = this.branding.userItalic ? 'italic' : 'normal';
      opacity = this.branding.userOpacity ?? 1;
      borderColor = this.branding.userBorderColor;
      borderWidth = this.branding.userBorderWidth;
    } else {
      bgColor = this.branding.aiBubbleBg || this.branding.bubbles?.aiBg || '#f1f5f9';
      textColor = this.branding.aiTextColor || this.branding.assistantTextColor || '#0f172a';
      border = this.branding.aiBubbleBorder || 'none';
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

  // Input field styles
  getInputStyle(): React.CSSProperties {
    const height = px(this.branding.inputHeight, 48);
    const radius = asDim(this.branding.inputRadius, '0.75rem');
    const fontSize = px(this.branding.inputFontSize, 14);
    const fontWeight = this.branding.inputBold ? '600' : 'normal';
    const fontStyle = this.branding.inputItalic ? 'italic' : 'normal';
    const bgColor = this.branding.inputBackgroundColor || this.branding.inputBg || '#ffffff';
    const textColor = this.branding.inputTextColor || '#0f172a';
    const primaryColor = this.branding.primaryColor || this.branding.colors?.primary || '#4f46e5';

    return {
      height,
      borderRadius: radius,
      backgroundColor: bgColor,
      color: textColor,
      fontSize,
      fontWeight,
      fontStyle,
      fontFamily: this.branding.fontFamily,
      '--focus-ring-color': primaryColor,
    } as React.CSSProperties & { '--focus-ring-color': string };
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