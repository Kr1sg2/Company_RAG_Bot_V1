import { useEffect, useState, useRef } from "react";
import { fetchPublicBranding, legacyChat } from "../lib/api";
import type { Branding } from "../lib/brandingTypes";
import { BrandingStyleMapper, avatarClassFromShape } from "../lib/brandingToStyles";
import { buildSystemPrompt } from "../lib/prompt";
import { speak, stopSpeak, createSTT } from "../lib/voice";
import { applyBrandingVars } from "../lib/theme";

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp: Date;
};


export default function ClientChat() {
  const [branding, setBranding] = useState<Partial<Branding> | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimited, setRateLimited] = useState(false);
  const [lastAssistantText, setLastAssistantText] = useState<string>('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const rateLimitTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Load branding on mount
  useEffect(() => {
    fetchPublicBranding()
      .then((raw: any) => {
        // Map multiple possible server field names -> our theming shape
        const resolvedShowBubbles =
          (typeof raw?.showBubbles === 'boolean') ? raw.showBubbles :
          (typeof raw?.hideBubbles === 'boolean') ? !raw.hideBubbles :
          (typeof raw?.bubblesEnabled === 'boolean') ? !!raw.bubblesEnabled :
          (raw?.bubbleStyle === 'none') ? false :
          (raw?.bubbleStyle === 'bubbles') ? true :
          undefined; // leave undefined to keep defaults

        const responseFormat =
          raw?.responseFormat ??
          raw?.responseStyle ??
          raw?.answerStyle ??
          'paragraphs';

        const normalized = {
          ...raw,

          // bubble colors (keep your existing fallbacks if you already have them)
          aiBubbleBg: raw?.aiBubbleBg ?? raw?.assistantBubbleBg ?? raw?.aiColor,
          aiTextColor: raw?.aiTextColor ?? raw?.assistantTextColor,
          userBubbleBg: raw?.userBubbleBg ?? raw?.userColor,
          userTextColor: raw?.userTextColor,

          // layout
          cardBackgroundColor: raw?.cardBackgroundColor ?? raw?.cardBg,
          cardOpacityPct: (raw?.cardOpacityPct ?? raw?.cardOpacity), // theme.ts now normalizes 0..1 or 0..100
          cardWidthPct: raw?.cardWidthPct ?? raw?.cardWidth,
          cardMaxWidthPct: raw?.cardMaxWidthPct ?? raw?.cardMaxWidth,
          chatOffsetTopPx: raw?.chatOffsetTopPx ?? raw?.chatOffsetTop,
          cardBorderRadiusPx: raw?.cardBorderRadiusPx ?? raw?.cardRadiusPx,

          // NEW: bubble visibility & shape
          showBubbles: resolvedShowBubbles,
          bubbleRadiusPx: raw?.bubbleRadiusPx ?? raw?.bubbleRadius,
          bubblePaddingX: raw?.bubblePaddingX ?? raw?.bubblePadX,
          bubblePaddingY: raw?.bubblePaddingY ?? raw?.bubblePadY,

          // bubble opacity (theme.ts already handles % vs fraction)
          aiOpacityPct: raw?.aiBubbleOpacityPct ?? raw?.aiOpacityPct ?? raw?.aiOpacity,
          userOpacityPct: raw?.userBubbleOpacityPct ?? raw?.userOpacityPct ?? raw?.userOpacity,

          // response format
          responseFormat: responseFormat,
        };

        setBranding(normalized);
        applyBrandingVars(normalized as any);
      })
      .catch(() => console.warn("Failed to load branding"));
  }, []);

  // Update favicon when branding changes
  useEffect(() => {
    if (!branding?.faviconUrl) return;
    const href = `${branding.faviconUrl}${branding.faviconUrl.includes('?') ? '&' : '?'}v=${Date.now()}`;
    let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.head.appendChild(link);
    }
    link.href = href;
  }, [branding?.faviconUrl]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const styleMapper = branding ? new BrandingStyleMapper(branding) : null;

  const handleSend = async () => {
    if (!input.trim() || isLoading || rateLimited) return;

    // Stop any current speech before sending
    stopSpeak();

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    // Rate limiting: Prevent spam
    setRateLimited(true);
    if (rateLimitTimeoutRef.current) {
      clearTimeout(rateLimitTimeoutRef.current);
    }
    rateLimitTimeoutRef.current = setTimeout(() => {
      setRateLimited(false);
    }, 2000); // 2 second cooldown

    try {
      const systemPrompt = branding ? buildSystemPrompt(branding as Branding) : undefined;
      const response = await legacyChat(userMessage.content, { system: systemPrompt });
      
      const assistantContent = (response.answer ?? response.reply);
      
      // Hide <ask>…</ask> from what we display but keep the behavior server-side
      const displayContent = assistantContent.replace(/<ask>[\s\S]*?<\/ask>/gi, '').trim();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: displayContent,
        sources: response.sources || [],
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setLastAssistantText(displayContent);
    } catch (err) {
      // Always show friendly error message in chat, never raw HTTP codes
      const friendlyMsg = "Sorry—something went wrong on the server. Please try again.";
      
      setError(friendlyMsg);
      
      // Add friendly error message to chat
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: friendlyMsg,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setError(null);
    inputRef.current?.focus();
  };

  const handleVoiceInput = () => {
    const stt = createSTT(setInput);
    if (stt.supported) {
      stt.start();
    }
  };

  const handleReadAloud = () => {
    if (lastAssistantText) {
      stopSpeak(); // Cancel any previous speech
      speak(lastAssistantText);
    }
  };

  if (!styleMapper) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-600">Loading chat interface...</div>
      </div>
    );
  }

  const pageStyle = styleMapper.getPageStyle();
  // Card styles now handled by CSS classes
  const titleStyle = styleMapper.getTitleStyle();
  const taglineStyle = styleMapper.getTaglineStyle();
  const chatAreaStyle = styleMapper.getChatAreaStyle();
  const inputStyle = styleMapper.getInputStyle();
  const buttonStyle = styleMapper.getButtonStyle(isLoading || rateLimited);
  const emptyStateStyle = styleMapper.getEmptyStateStyle();
  const sourceLinkStyle = styleMapper.getSourceLinkStyle();
  const loadingStyle = styleMapper.getLoadingStyle();

  // A lightweight alert style that respects branding (re-use muted/empty state colors)
  const alertTextStyle = emptyStateStyle;

  const customInputStyle: React.CSSProperties = {
    borderRadius: branding?.inputBorderRadius ?? 12,
    paddingLeft: branding?.inputPaddingX ?? 12,
    paddingRight: branding?.inputPaddingX ?? 12,
    paddingTop: branding?.inputPaddingY ?? 10,
    paddingBottom: branding?.inputPaddingY ?? 10,
    borderWidth: branding?.inputBorderWidth ?? 1,
    borderStyle: 'solid',
    borderColor: branding?.inputBorderColor ?? '#D1D5DB',
  };

  return (
    <div style={pageStyle} className="min-h-screen w-full p-4">
      {/* Inject placeholder color styling */}
      <style>
        {`
          .chat-input::placeholder {
            color: ${(inputStyle as any)['--placeholder-color']} !important;
          }
        `}
      </style>
      <div className="chat-card">
        <div className="chat-card-inner">
        {/* Header */}
        <div className="text-center mb-6">
          {branding?.logoDataUrl && (
            <img
              src={branding.logoDataUrl}
              alt="Logo"
              className="mx-auto mb-4 max-h-16 w-auto"
            />
          )}
          <h1 style={titleStyle}>
            {branding?.companyName || "Company Chat"}
          </h1>
          <p style={taglineStyle} className="mt-1">
            {branding?.taglineText || "Ask questions about your company documents."}
          </p>
        </div>

        {/* Chat Area */}
        <div style={chatAreaStyle} className="mb-4 overflow-y-auto border rounded-lg">
          <div className="p-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <p style={emptyStateStyle}>
                  {branding?.emptyStateText || 'Start by asking something like "What is the company dress code?"'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    styleMapper={styleMapper}
                    sourceLinkStyle={sourceLinkStyle}
                    branding={branding || {}}
                  />
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    {styleMapper.shouldShowAvatar('assistant') && styleMapper.getAvatarPosition('assistant') === 'left' && (
                      <AvatarImage styleMapper={styleMapper} />
                    )}
                    <div className="bubble assistant flex items-center gap-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span style={loadingStyle} className="text-xs">Thinking...</span>
                    </div>
                  </div>
                )}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Error Display (branding-aware, no hardcoded red theme) */}
        {error && (
          <div className="mb-4 p-3 border rounded-lg text-sm" style={alertTextStyle}>
            <div className="flex justify-between items-start">
              <span>{error}</span>
              <button 
                onClick={() => setError(null)}
                className="ml-2"
                style={alertTextStyle}
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={branding?.inputPlaceholder || "Type your question and press Enter…"}
            style={{...inputStyle, ...customInputStyle}}
            className="flex-1 outline-none chat-input"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading || rateLimited}
            style={buttonStyle}
            className="px-6 font-medium transition-all duration-200 rounded-lg"
          >
            {isLoading ? 'Sending...' : styleMapper.getSendButtonText()}
          </button>
          
          {messages.length > 0 && (
            <button
              onClick={clearConversation}
              style={buttonStyle}
              className="px-4 py-2 rounded-lg transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {/* Rate limit indicator (branding-aware text) */}
        {rateLimited && (
          <div className="mt-2 text-center text-xs" style={emptyStateStyle}>
            Please wait before sending another message...
          </div>
        )}

        {/* Audio Controls (branding-aware buttons, if enabled) */}
        {branding?.showAudioControls && (branding?.enableTextToSpeech || branding?.enableSpeechToText) && (
          <div className="mt-4 flex gap-2 justify-center">
            {branding?.enableSpeechToText && (
              <button 
                onClick={handleVoiceInput}
                style={buttonStyle} 
                className="px-3 py-2 text-sm rounded-lg transition-colors"
              >
                🎤 Voice Input
              </button>
            )}
            {branding?.enableTextToSpeech && (
              <button 
                onClick={handleReadAloud}
                style={buttonStyle} 
                className="px-3 py-2 text-sm rounded-lg transition-colors"
              >
                🔊 Read Aloud
              </button>
            )}
          </div>
        )}
        </div>
      </div>
    </div>
  );
}

// Message Bubble Component
const MessageBubble = ({ 
  message, 
  styleMapper, 
  sourceLinkStyle,
  branding
}: { 
  message: Message; 
  styleMapper: BrandingStyleMapper;
  sourceLinkStyle: React.CSSProperties;
  branding: Partial<Branding>;
}) => {
  const isUser = message.role === 'user';
  // Use CSS classes instead of inline styles for bubble colors
  const bubbleClasses = `bubble ${message.role === 'assistant' ? 'assistant' : 'user'}`;
  
  // User avatar handling
  const showUserAvatar = Boolean(isUser && branding?.userAvatarImageUrl && (branding?.showUserAvatarOnMobile ?? true));
  const userAvatarSize = Math.max(16, branding?.userAvatarSize ?? 40);
  const userAvatarClass = avatarClassFromShape(branding?.userAvatarShape);
  const mobileHide = (branding?.showUserAvatarOnMobile === false) ? 'hidden sm:block' : '';
  const userRight = (branding?.userAvatarPosition ?? 'right') === 'right';

  const userAvatarImg = showUserAvatar ? (
    <img 
      src={branding!.userAvatarImageUrl!} 
      alt="You"
      className={`shrink-0 ${mobileHide} ${userAvatarClass} object-cover`}
      style={{ width: userAvatarSize, height: userAvatarSize }}
    />
  ) : null;

  // Assistant avatar handling (existing logic)
  const shouldShowAssistantAvatar = styleMapper.shouldShowAvatar('assistant');
  const assistantAvatarPosition = styleMapper.getAvatarPosition('assistant');

  return (
    <div className={`flex items-start gap-2 ${isUser && userRight ? 'justify-end' : 'justify-start'}`}>
      {/* Left avatars */}
      {!isUser && shouldShowAssistantAvatar && assistantAvatarPosition === 'left' && (
        <AvatarImage styleMapper={styleMapper} />
      )}
      {isUser && !userRight && userAvatarImg}
      
      {/* Message Content */}
      <div className="max-w-[75%]">
        <div className={bubbleClasses}>
          <div className="whitespace-pre-wrap break-words">
            {message.content}
          </div>
          
          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 pt-3 border-t border-current opacity-70">
              <div className="text-xs font-medium mb-1">Sources:</div>
              <div className="space-y-1">
                {message.sources.map((source: any, idx: number) => {
                  // Handle different source formats from API
                  let href = source.url || source.href || source.link || source.file_url || source.source;
                  const label = source.name || source.label || source.title || href || `Source ${idx + 1}`;
                  
                  // Ensure absolute URL for /files/ routes to bypass SPA router
                  if (href && href.startsWith('/files/')) {
                    href = `${window.location.origin}${href}`;
                  }
                  
                  return (
                    <div key={idx}>
                      {href ? (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={sourceLinkStyle}
                          className="text-xs hover:opacity-80 underline break-all"
                        >
                          {label}
                        </a>
                      ) : (
                        <span className="text-xs opacity-70">
                          {label}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          
          {/* Timestamp */}
          <div className="text-xs opacity-50 mt-2">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Right avatars */}
      {!isUser && shouldShowAssistantAvatar && assistantAvatarPosition === 'right' && (
        <AvatarImage styleMapper={styleMapper} />
      )}
      {isUser && userRight && userAvatarImg}
    </div>
  );
};

// Avatar Image Component
const AvatarImage = ({ 
  styleMapper 
}: { 
  styleMapper: BrandingStyleMapper;
}) => {
  const avatarUrl = styleMapper.getAvatarImageUrl();
  const avatarStyle = styleMapper.getAvatarStyle();
  
  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt="Assistant"
        style={avatarStyle}
        className="object-cover flex-shrink-0"
      />
    );
  }
  
  return (
    <div 
      style={avatarStyle} 
      className="rounded-full flex-shrink-0 flex items-center justify-center"
    >
      🤖
    </div>
  );
};

