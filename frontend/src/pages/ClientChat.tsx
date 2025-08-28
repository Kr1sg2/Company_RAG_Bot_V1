import { useEffect, useState } from "react";
import { fetchPublicBranding, chat, type Branding } from "../lib/api";

// Default branding values
const defaultBranding: Branding = {
  companyName: "AI Company Chatbot",
  taglineText: "",
  emptyStateText: "Ask me anything about your company!",
  inputPlaceholder: "Ask a question...",
  logoDataUrl: null,
  faviconUrl: null,
  pageBackgroundUrl: null,
  chatCardBackgroundUrl: null,
  colors: { primary: "#000000", accent: "#0066cc", bg: "#ffffff", text: "#000000" },
  bubbles: { radius: "12px", aiBg: "#f3f4f6", userBg: "#0066cc" },
  chatWidth: "800",
  chatHeight: "80",
  chatOffsetTop: "4",
  cardRadius: "16",
  cardBg: "rgba(255,255,255,0.88)",
  
  // Fonts - Typography defaults
  fontFamily: "system-ui",
  titleFontSize: 32,
  bodyFontSize: 16,
  titleBold: true,
  titleItalic: false,
  taglineFontSize: 18,
  taglineBold: false,
  taglineItalic: false,
  
  // Enhanced Bubble defaults
  bubblePadding: 12,
  bubbleMaxWidth: 70,
  aiTextColor: "#000000",
  aiBubbleBorder: "none",
  userTextColor: "#ffffff",
  userBubbleBorder: "none",
  
  // Enhanced Card defaults
  cardPadding: 24,
  inputHeight: 44,
  inputRadius: 8,
  messageSpacing: 16,
  
  // Backgrounds & Shadows defaults
  pageBackgroundColor: "#ffffff",
  cardBackgroundColor: "#ffffff",
  cardOpacity: 100,
  shadowColor: "#000000",
  shadowBlur: 10,
  shadowSpread: 0,
  shadowOpacity: 20,
  enableShadow: true,
  enableGlow: false,
  
  // Robot / Avatar defaults
  avatarImageUrl: null,
  avatarSize: 40,
  avatarPosition: "left",
  avatarShape: "circle",
  showAvatarOnMobile: true,
  
  // Audio / TTS & STT defaults
  enableTextToSpeech: false,
  enableSpeechToText: false,
  ttsVoice: "default",
  ttsSpeed: 1.0,
  sttLanguage: "en-US",
  sttAutoSend: false,
  showAudioControls: true,
  ttsAutoPlay: false,
  
  // LLM Controls defaults
  aiModel: "gpt-4",
  aiTemperature: 0.7,
  aiMaxTokens: 2048,
  aiTopK: 50,
  aiStrictness: "balanced",
  aiSystemPrompt: "You are a helpful AI assistant.",
  aiStreamResponses: true,
  aiRetainContext: true,
};

// Simple chat component
function SimpleChat({ branding }: { branding: Branding }) {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const result = await chat(userMessage);
      setMessages(prev => [...prev, { role: 'assistant', content: result.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div 
      className="flex flex-col h-full"
      style={{ 
        maxWidth: `${branding.chatWidth}px`,
        height: `${branding.chatHeight}vh`,
        backgroundColor: branding.cardBg,
        padding: `${branding.cardPadding || 24}px`,
        fontFamily: branding.fontFamily || "system-ui",
        fontSize: `${branding.bodyFontSize || 16}px`,
      }}
    >
      {/* Messages */}
      <div 
        className="flex-1 overflow-y-auto"
        style={{ 
          marginBottom: `${branding.messageSpacing || 16}px`,
        }}
      >
        {messages.length === 0 ? (
          <div 
            className="text-center py-8"
            style={{ 
              color: branding.colors.text,
              fontSize: `${branding.bodyFontSize || 16}px`,
            }}
          >
            {branding.emptyStateText}
          </div>
        ) : (
          <div 
            className="space-y-4"
            style={{ gap: `${branding.messageSpacing || 16}px` }}
          >
            {messages.map((message, i) => (
              <div key={i} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} items-end gap-2`}>
                {/* AI Avatar - Left */}
                {message.role === 'assistant' && branding.avatarPosition === 'left' && branding.avatarImageUrl && (
                  <img
                    src={branding.avatarImageUrl}
                    alt="AI Assistant"
                    className={`${branding.showAvatarOnMobile ? '' : 'hidden sm:block'} flex-shrink-0`}
                    style={{
                      width: `${branding.avatarSize || 40}px`,
                      height: `${branding.avatarSize || 40}px`,
                      borderRadius: branding.avatarShape === 'circle' ? '50%' 
                        : branding.avatarShape === 'rounded' ? '8px' : '0px',
                    }}
                  />
                )}

                <div
                  style={{
                    maxWidth: `${branding.bubbleMaxWidth || 70}%`,
                    padding: `${branding.bubblePadding || 12}px`,
                    backgroundColor: message.role === 'user' ? branding.bubbles.userBg : branding.bubbles.aiBg,
                    borderRadius: branding.bubbles.radius,
                    color: message.role === 'user' 
                      ? (branding.userTextColor || "#ffffff")
                      : (branding.aiTextColor || "#000000"),
                    border: message.role === 'user' 
                      ? (branding.userBubbleBorder || "none")
                      : (branding.aiBubbleBorder || "none"),
                    fontSize: `${branding.bodyFontSize || 16}px`,
                    fontFamily: branding.fontFamily || "system-ui",
                  }}
                >
                  {message.content}
                </div>

                {/* AI Avatar - Right */}
                {message.role === 'assistant' && branding.avatarPosition === 'right' && branding.avatarImageUrl && (
                  <img
                    src={branding.avatarImageUrl}
                    alt="AI Assistant"
                    className={`${branding.showAvatarOnMobile ? '' : 'hidden sm:block'} flex-shrink-0`}
                    style={{
                      width: `${branding.avatarSize || 40}px`,
                      height: `${branding.avatarSize || 40}px`,
                      borderRadius: branding.avatarShape === 'circle' ? '50%' 
                        : branding.avatarShape === 'rounded' ? '8px' : '0px',
                    }}
                  />
                )}
              </div>
            ))}
          </div>
        )}
        {loading && (
          <div className="flex justify-start items-end gap-2 mt-4">
            {/* AI Avatar - Left */}
            {branding.avatarPosition === 'left' && branding.avatarImageUrl && (
              <img
                src={branding.avatarImageUrl}
                alt="AI Assistant"
                className={`${branding.showAvatarOnMobile ? '' : 'hidden sm:block'} flex-shrink-0`}
                style={{
                  width: `${branding.avatarSize || 40}px`,
                  height: `${branding.avatarSize || 40}px`,
                  borderRadius: branding.avatarShape === 'circle' ? '50%' 
                    : branding.avatarShape === 'rounded' ? '8px' : '0px',
                }}
              />
            )}

            <div
              style={{
                maxWidth: `${branding.bubbleMaxWidth || 70}%`,
                padding: `${branding.bubblePadding || 12}px`,
                backgroundColor: branding.bubbles.aiBg,
                borderRadius: branding.bubbles.radius,
                color: branding.aiTextColor || "#000000",
                border: branding.aiBubbleBorder || "none",
                fontSize: `${branding.bodyFontSize || 16}px`,
                fontFamily: branding.fontFamily || "system-ui",
              }}
            >
              Thinking...
            </div>

            {/* AI Avatar - Right */}
            {branding.avatarPosition === 'right' && branding.avatarImageUrl && (
              <img
                src={branding.avatarImageUrl}
                alt="AI Assistant"
                className={`${branding.showAvatarOnMobile ? '' : 'hidden sm:block'} flex-shrink-0`}
                style={{
                  width: `${branding.avatarSize || 40}px`,
                  height: `${branding.avatarSize || 40}px`,
                  borderRadius: branding.avatarShape === 'circle' ? '50%' 
                    : branding.avatarShape === 'rounded' ? '8px' : '0px',
                }}
              />
            )}
          </div>
        )}
      </div>
      
      {/* Input */}
      <div>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={branding.inputPlaceholder}
            style={{
              height: `${branding.inputHeight || 44}px`,
              borderRadius: `${branding.inputRadius || 8}px`,
              fontSize: `${branding.bodyFontSize || 16}px`,
              fontFamily: branding.fontFamily || "system-ui",
            }}
            className="flex-1 px-3 border focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{
              height: `${branding.inputHeight || 44}px`,
              borderRadius: `${branding.inputRadius || 8}px`,
              backgroundColor: branding.colors.accent || "#0066cc",
              fontSize: `${branding.bodyFontSize || 16}px`,
              fontFamily: branding.fontFamily || "system-ui",
            }}
            className="px-4 text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ClientChatPage() {
  const [branding, setBranding] = useState<Branding>(defaultBranding);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const data = await fetchPublicBranding();
        if (!alive) return;
        
        setBranding(data);
        
        // Apply basic styling
        if (data.companyName) {
          document.title = data.companyName;
        }
        
        // Apply favicon if provided
        if (data.faviconUrl) {
          const head = document.head || document.getElementsByTagName("head")[0];
          const existingIcon = head.querySelector('link[rel="icon"]');
          if (existingIcon) existingIcon.remove();
          
          const link = document.createElement("link");
          link.rel = "icon";
          link.href = data.faviconUrl;
          head.appendChild(link);
        }
      } catch (error) {
        console.error("Failed to load branding:", error);
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();

    return () => {
      alive = false;
    };
  }, []);

  if (loading) {
    return <div className="p-6">Loading…</div>;
  }

  // Generate card shadow/glow CSS
  const cardShadow = () => {
    if (!branding.enableShadow && !branding.enableGlow) return "none";
    
    const shadowParts = [];
    
    if (branding.enableShadow) {
      const shadowOpacity = (branding.shadowOpacity || 20) / 100;
      const shadowColor = branding.shadowColor || "#000000";
      const blur = branding.shadowBlur || 10;
      const spread = branding.shadowSpread || 0;
      
      // Convert hex to rgba for opacity
      const hexToRgba = (hex: string, alpha: number) => {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
      };
      
      shadowParts.push(`0 4px ${blur}px ${spread}px ${hexToRgba(shadowColor, shadowOpacity)}`);
    }
    
    if (branding.enableGlow) {
      const glowColor = branding.colors.accent || "#0066cc";
      shadowParts.push(`0 0 20px ${glowColor}33`);
    }
    
    return shadowParts.join(", ");
  };

  // Generate card background with opacity
  const cardBackground = () => {
    if (branding.cardBg && branding.cardBg !== "rgba(255,255,255,0.88)") {
      return branding.cardBg; // Use CSS override if provided
    }
    
    const opacity = (branding.cardOpacity || 100) / 100;
    const baseColor = branding.cardBackgroundColor || "#ffffff";
    
    // Convert hex to rgba
    const hexToRgba = (hex: string, alpha: number) => {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    };
    
    return hexToRgba(baseColor, opacity);
  };

  return (
    <div 
      className="min-h-screen w-full p-4 sm:p-6"
      style={{ 
        backgroundColor: branding.pageBackgroundColor || branding.colors.bg,
        backgroundImage: branding.pageBackgroundUrl ? `url(${branding.pageBackgroundUrl})` : "none",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        color: branding.colors.text 
      }}
    >
      <div className="max-w-3xl mx-auto">
        <header className="text-center mb-6">
          {branding.logoDataUrl && (
            <img
              src={branding.logoDataUrl}
              alt=""
              style={{ height: 52 }}
              className="mx-auto mb-2"
            />
          )}

          <h1 
            className="mb-1"
            style={{
              fontSize: `${branding.titleFontSize || 32}px`,
              fontWeight: branding.titleBold ? "bold" : "normal",
              fontStyle: branding.titleItalic ? "italic" : "normal",
              fontFamily: branding.fontFamily || "system-ui",
              color: branding.colors.text,
            }}
          >
            {branding.companyName || "AI Company Chatbot"}
          </h1>

          {branding.taglineText && (
            <p 
              className="opacity-80"
              style={{
                fontSize: `${branding.taglineFontSize || 18}px`,
                fontWeight: branding.taglineBold ? "bold" : "normal",
                fontStyle: branding.taglineItalic ? "italic" : "normal",
                fontFamily: branding.fontFamily || "system-ui",
                color: branding.colors.text,
              }}
            >
              {branding.taglineText}
            </p>
          )}
        </header>

        <div 
          className="rounded-2xl mx-auto"
          style={{
            backgroundColor: cardBackground(),
            backgroundImage: branding.chatCardBackgroundUrl ? `url(${branding.chatCardBackgroundUrl})` : "none",
            backgroundSize: "cover",
            backgroundPosition: "center",
            borderRadius: `${branding.cardRadius}px`,
            maxWidth: `${branding.chatWidth}px`,
            boxShadow: cardShadow(),
          }}
        >
          <SimpleChat branding={branding} />
        </div>
      </div>
    </div>
  );
}

