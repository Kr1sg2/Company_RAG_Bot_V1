import type { Branding } from './brandingTypes';
import { getBrandingValue } from './brandingTypes';

// Helper functions
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

// Convert branding settings to CSS styles for consistent application
export class BrandingStyleMapper {
  private branding: Partial<Branding>;
  
  constructor(branding: Partial<Branding>) {
    this.branding = branding;
  }

  // Page-level styles
  getPageStyle(): React.CSSProperties {
    const bg = getBrandingValue(this.branding, 'pageBackgroundColor');
    const bgUrl = getBrandingValue(this.branding, 'pageBackgroundUrl');
    const fontFamily = getBrandingValue(this.branding, 'fontFamily');
    
    return {
      background: bgUrl 
        ? `url(${bgUrl}) center/cover no-repeat`
        : bg,
      fontFamily,
      minHeight: '100vh',
    };
  }

  // Chat card container styles
  getCardStyle(): React.CSSProperties {
    const width = getBrandingValue(this.branding, 'chatWidth');
    const radius = getBrandingValue(this.branding, 'cardRadius');
    const bgColor = getBrandingValue(this.branding, 'cardBackgroundColor');
    const bgUrl = getBrandingValue(this.branding, 'cardBackgroundUrl');
    const padding = getBrandingValue(this.branding, 'cardPadding');
    const opacity = getBrandingValue(this.branding, 'cardOpacity');
    const enableShadow = getBrandingValue(this.branding, 'enableShadow');
    const shadowColor = getBrandingValue(this.branding, 'shadowColor');
    const shadowBlur = getBrandingValue(this.branding, 'shadowBlur');
    const shadowSpread = getBrandingValue(this.branding, 'shadowSpread');
    const shadowOpacity = getBrandingValue(this.branding, 'shadowOpacity');
    const enableGlow = getBrandingValue(this.branding, 'enableGlow');

    const shadowRgba = this.hexToRgba(shadowColor, asOpacity(shadowOpacity, 20));
    const boxShadow = enableShadow 
      ? `0 ${px(shadowSpread, 0)} ${px(shadowBlur, 10)} ${shadowRgba}`
      : 'none';
    
    const glowShadow = enableGlow 
      ? `0 0 20px ${this.hexToRgba(getBrandingValue(this.branding, 'colors')?.primary || '#4f46e5', 0.3)}`
      : '';

    const combinedShadow = [boxShadow, glowShadow].filter(s => s && s !== 'none').join(', ') || 'none';

    return {
      maxWidth: asDim(width, '64rem'),
      borderRadius: asDim(radius, '1rem'),
      backgroundColor: bgUrl ? 'transparent' : this.adjustOpacity(bgColor, asOpacity(opacity, 90)),
      backgroundImage: bgUrl ? `url(${bgUrl})` : undefined,
      backgroundSize: bgUrl ? 'cover' : undefined,
      backgroundPosition: bgUrl ? 'center' : undefined,
      border: '1px solid rgb(226 232 240)',
      backdropFilter: 'blur(8px)',
      padding: px(padding, 0),
      boxShadow: combinedShadow,
    };
  }

  // Title styles
  getTitleStyle(): React.CSSProperties {
    const fontSize = getBrandingValue(this.branding, 'titleFontSize');
    const bold = getBrandingValue(this.branding, 'titleBold');
    const italic = getBrandingValue(this.branding, 'titleItalic');
    const color = getBrandingValue(this.branding, 'textColor');

    return {
      fontSize: px(fontSize, 20),
      fontWeight: bold ? '600' : 'normal',
      fontStyle: italic ? 'italic' : 'normal',
      color,
    };
  }

  // Tagline styles
  getTaglineStyle(): React.CSSProperties {
    const fontSize = getBrandingValue(this.branding, 'taglineFontSize');
    const bold = getBrandingValue(this.branding, 'taglineBold');
    const italic = getBrandingValue(this.branding, 'taglineItalic');
    const color = getBrandingValue(this.branding, 'mutedTextColor');

    return {
      fontSize: px(fontSize, 14),
      fontWeight: bold ? '600' : 'normal',
      fontStyle: italic ? 'italic' : 'normal',
      color,
    };
  }

  // Chat area styles
  getChatAreaStyle(): React.CSSProperties {
    const height = getBrandingValue(this.branding, 'chatHeight');
    const offsetTop = getBrandingValue(this.branding, 'chatOffsetTop');

    return {
      height: asDim(height, '60vh'),
      paddingTop: px(offsetTop, 16),
    };
  }

  // Message bubble styles
  getBubbleStyle(role: 'user' | 'assistant'): React.CSSProperties {
    const maxWidth = getBrandingValue(this.branding, 'bubbleMaxWidth');
    const radius = getBrandingValue(this.branding, 'bubbles')?.radius || 
                   getBrandingValue(this.branding, 'bubbleRadius');
    const padding = getBrandingValue(this.branding, 'bubblePadding');
    const spacing = getBrandingValue(this.branding, 'messageSpacing');

    const bgColor = role === 'user' 
      ? getBrandingValue(this.branding, 'bubbles')?.userBg || 
        getBrandingValue(this.branding, 'userBubbleBg')
      : getBrandingValue(this.branding, 'bubbles')?.aiBg || 
        getBrandingValue(this.branding, 'aiBubbleBg');

    const textColor = role === 'user' 
      ? getBrandingValue(this.branding, 'userTextColor')
      : getBrandingValue(this.branding, 'aiTextColor');

    const border = role === 'user'
      ? getBrandingValue(this.branding, 'userBubbleBorder')
      : getBrandingValue(this.branding, 'aiBubbleBorder');

    return {
      maxWidth: asPercent(maxWidth, 70),
      borderRadius: asDim(radius, '1rem'),
      padding: px(padding, 12),
      backgroundColor: bgColor,
      color: textColor,
      border: border === 'none' ? undefined : border,
      borderBottomRightRadius: role === 'user' ? '4px' : undefined,
      borderBottomLeftRadius: role === 'assistant' ? '4px' : undefined,
      marginBottom: px(spacing, 16),
    };
  }

  // Input styles
  getInputStyle(): React.CSSProperties {
    const height = getBrandingValue(this.branding, 'inputHeight');
    const radius = getBrandingValue(this.branding, 'inputRadius');
    const primaryColor = getBrandingValue(this.branding, 'colors')?.primary;

    return {
      height: px(height, 48),
      borderRadius: asDim(radius, '0.75rem'),
      // Focus ring color from primary
      '--focus-ring-color': primaryColor,
    } as React.CSSProperties & { '--focus-ring-color': string };
  }

  // Button styles
  getButtonStyle(disabled: boolean = false): React.CSSProperties {
    const height = getBrandingValue(this.branding, 'inputHeight');
    const radius = getBrandingValue(this.branding, 'inputRadius');
    const primaryColor = getBrandingValue(this.branding, 'colors')?.primary;
    const accentColor = getBrandingValue(this.branding, 'colors')?.accent;

    return {
      height: px(height, 48),
      borderRadius: asDim(radius, '0.75rem'),
      backgroundColor: disabled ? '#94a3b8' : primaryColor,
      cursor: disabled ? 'not-allowed' : 'pointer',
      '--hover-color': accentColor,
    } as React.CSSProperties & { '--hover-color': string };
  }

  // Avatar styles
  getAvatarStyle(): React.CSSProperties {
    const size = getBrandingValue(this.branding, 'avatarSize');
    const shape = getBrandingValue(this.branding, 'avatarShape');
    
    const borderRadius = shape === 'circle' ? '50%' : 
                        shape === 'rounded' ? '0.5rem' : 
                        '0';

    return {
      width: px(size, 40),
      height: px(size, 40),
      borderRadius,
    };
  }

  // Utility methods
  private hexToRgba(hex: string, alpha: number): string {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return `rgba(0, 0, 0, ${alpha})`;
    
    const r = parseInt(result[1], 16);
    const g = parseInt(result[2], 16);
    const b = parseInt(result[3], 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  private adjustOpacity(color: string, opacity: number): string {
    if (color.startsWith('rgba(')) {
      return color.replace(/[\d\.]+\)$/, `${opacity})`);
    }
    if (color.startsWith('rgb(')) {
      return color.replace('rgb(', 'rgba(').replace(')', `, ${opacity})`);
    }
    if (color.startsWith('#')) {
      return this.hexToRgba(color, opacity);
    }
    return color;
  }
}

// Convenience function for creating style mapper
export function createStyleMapper(branding: Partial<Branding>): BrandingStyleMapper {
  return new BrandingStyleMapper(branding);
}

// Direct style generation functions for common use cases
export function getPageStyles(branding: Partial<Branding>): React.CSSProperties {
  return new BrandingStyleMapper(branding).getPageStyle();
}

export function getCardStyles(branding: Partial<Branding>): React.CSSProperties {
  return new BrandingStyleMapper(branding).getCardStyle();
}

export function getBubbleStyles(branding: Partial<Branding>, role: 'user' | 'assistant'): React.CSSProperties {
  return new BrandingStyleMapper(branding).getBubbleStyle(role);
}