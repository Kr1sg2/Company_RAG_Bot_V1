"""
Thread-safe settings store for FastAPI backend.
Handles persistence to storage/settings.json with proper defaults and field extraction.
"""

from pathlib import Path
import json
import threading
from typing import Dict, Any

# Thread-safe file operations
_lock = threading.Lock()
SETTINGS_FILE = Path("storage/settings.json")

def load_settings() -> Dict[str, Any]:
    """Load all settings from storage/settings.json, return empty dict if missing."""
    with _lock:
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError, IOError):
                return {}
        return {}

def save_settings(data: Dict[str, Any]) -> None:
    """Persist full settings to disk, ensure directory exists."""
    with _lock:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def extract_branding_fields(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only branding-related fields with defaults."""
    branding = {
        # Basic Settings
        "companyName": settings.get("companyName", "Leaders AI Company Chatbot"),
        "taglineText": settings.get("taglineText", "Closed-book RAG system - answers only from company documents"),
        "emptyStateText": settings.get("emptyStateText", "Ask me anything about your company documents!"),
        "inputPlaceholder": settings.get("inputPlaceholder", "Ask a question about your documents..."),
        "logoDataUrl": settings.get("logoDataUrl"),
        "faviconUrl": settings.get("faviconUrl"),
        "pageBackgroundUrl": settings.get("pageBackgroundUrl"),
        "chatCardBackgroundUrl": settings.get("chatCardBackgroundUrl"),
        
        # Colors
        "colors": settings.get("colors", {
            "primary": "#6190ff",
            "accent": "#756bff",
            "bg": "#0b1020",
            "text": "#e6e6e6"
        }),
        "bubbles": settings.get("bubbles", {
            "radius": "18px",
            "aiBg": "#0f1530",
            "userBg": "#1b2447"
        }),
        
        # Original dimensions
        "chatWidth": settings.get("chatWidth", "920"),
        "chatHeight": settings.get("chatHeight", "56"),
        "chatOffsetTop": settings.get("chatOffsetTop", "7"),
        "cardRadius": settings.get("cardRadius", "18"),
        "cardBg": settings.get("cardBg", "rgba(255,255,255,0.88)"),
        
        # NEW: Fonts - Typography
        "fontFamily": settings.get("fontFamily", "system-ui"),
        "titleFontSize": settings.get("titleFontSize", 32),
        "bodyFontSize": settings.get("bodyFontSize", 16),
        "titleBold": settings.get("titleBold", True),
        "titleItalic": settings.get("titleItalic", False),
        "taglineFontSize": settings.get("taglineFontSize", 18),
        "taglineBold": settings.get("taglineBold", False),
        "taglineItalic": settings.get("taglineItalic", False),
        
        # NEW: Enhanced Bubble Controls
        "bubblePadding": settings.get("bubblePadding", 12),
        "bubbleMaxWidth": settings.get("bubbleMaxWidth", 70),
        "aiTextColor": settings.get("aiTextColor", "#000000"),
        "aiBubbleBorder": settings.get("aiBubbleBorder", "none"),
        "userTextColor": settings.get("userTextColor", "#ffffff"),
        "userBubbleBorder": settings.get("userBubbleBorder", "none"),
        
        # NEW: Enhanced Card Controls
        "cardPadding": settings.get("cardPadding", 24),
        "inputHeight": settings.get("inputHeight", 44),
        "inputRadius": settings.get("inputRadius", 8),
        "messageSpacing": settings.get("messageSpacing", 16),
        
        # NEW: Backgrounds & Shadows
        "pageBackgroundColor": settings.get("pageBackgroundColor", "#ffffff"),
        "cardBackgroundColor": settings.get("cardBackgroundColor", "#ffffff"),
        "cardOpacity": settings.get("cardOpacity", 100),
        "shadowColor": settings.get("shadowColor", "#000000"),
        "shadowBlur": settings.get("shadowBlur", 10),
        "shadowSpread": settings.get("shadowSpread", 0),
        "shadowOpacity": settings.get("shadowOpacity", 20),
        "enableShadow": settings.get("enableShadow", True),
        "enableGlow": settings.get("enableGlow", False),
        
        # NEW: Robot / Avatar
        "avatarImageUrl": settings.get("avatarImageUrl"),
        "avatarSize": settings.get("avatarSize", 40),
        "avatarPosition": settings.get("avatarPosition", "left"),
        "avatarShape": settings.get("avatarShape", "circle"),
        "showAvatarOnMobile": settings.get("showAvatarOnMobile", True),
        
        # NEW: Audio / TTS & STT
        "enableTextToSpeech": settings.get("enableTextToSpeech", False),
        "enableSpeechToText": settings.get("enableSpeechToText", False),
        "ttsVoice": settings.get("ttsVoice", "default"),
        "ttsSpeed": settings.get("ttsSpeed", 1.0),
        "sttLanguage": settings.get("sttLanguage", "en-US"),
        "sttAutoSend": settings.get("sttAutoSend", False),
        "showAudioControls": settings.get("showAudioControls", True),
        "ttsAutoPlay": settings.get("ttsAutoPlay", False),
        
        # NEW: LLM Controls
        "aiModel": settings.get("aiModel", "gpt-4"),
        "aiTemperature": settings.get("aiTemperature", 0.7),
        "aiMaxTokens": settings.get("aiMaxTokens", 2048),
        "aiTopK": settings.get("aiTopK", 50),
        "aiStrictness": settings.get("aiStrictness", "balanced"),
        "aiSystemPrompt": settings.get("aiSystemPrompt", "You are a helpful AI assistant."),
        "aiStreamResponses": settings.get("aiStreamResponses", True),
        "aiRetainContext": settings.get("aiRetainContext", True)
    }
    # Remove None values
    return {k: v for k, v in branding.items() if v is not None}

def extract_ai_fields(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only AI settings with defaults."""
    return {
        "temperature": settings.get("temperature", 0.7),
        "top_k": settings.get("top_k", 40),
        "max_tokens": settings.get("max_tokens", 1024),
        "strictness": settings.get("strictness", 1),
        "enableSpeechToText": settings.get("enableSpeechToText", True),
        "enableTextToSpeech": settings.get("enableTextToSpeech", False),
        "voice": settings.get("voice", "alloy"),
        "model": settings.get("model", "gpt-4o-mini"),
        "sttEnabled": settings.get("sttEnabled", True),
        "sttLanguage": settings.get("sttLanguage", "en-US"),
        "sttAutoSend": settings.get("sttAutoSend", False)
    }

def extract_full_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Extract complete settings (merge branding + AI)."""
    full = {}
    full.update(extract_branding_fields(settings))
    full.update(extract_ai_fields(settings))
    return full

def update_branding_fields(branding_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update only allowed branding fields, preserving other settings."""
    allowed_fields = {
        # Basic Settings
        "companyName", "taglineText", "emptyStateText", "inputPlaceholder",
        "logoDataUrl", "faviconUrl", "pageBackgroundUrl", "chatCardBackgroundUrl",
        "colors", "bubbles", "chatWidth", "chatHeight", "chatOffsetTop", 
        "cardRadius", "cardBg",
        
        # Fonts - Typography
        "fontFamily", "titleFontSize", "bodyFontSize", "titleBold", "titleItalic",
        "taglineFontSize", "taglineBold", "taglineItalic",
        
        # Enhanced Bubble Controls
        "bubblePadding", "bubbleMaxWidth", "aiTextColor", "aiBubbleBorder",
        "userTextColor", "userBubbleBorder",
        
        # Enhanced Card Controls
        "cardPadding", "inputHeight", "inputRadius", "messageSpacing",
        
        # Backgrounds & Shadows
        "pageBackgroundColor", "cardBackgroundColor", "cardOpacity", "shadowColor",
        "shadowBlur", "shadowSpread", "shadowOpacity", "enableShadow", "enableGlow",
        
        # Robot / Avatar
        "avatarImageUrl", "avatarSize", "avatarPosition", "avatarShape", "showAvatarOnMobile",
        
        # Audio / TTS & STT
        "enableTextToSpeech", "enableSpeechToText", "ttsVoice", "ttsSpeed",
        "sttLanguage", "sttAutoSend", "showAudioControls", "ttsAutoPlay",
        
        # LLM Controls
        "aiModel", "aiTemperature", "aiMaxTokens", "aiTopK", "aiStrictness",
        "aiSystemPrompt", "aiStreamResponses", "aiRetainContext"
    }
    
    settings = load_settings()
    for field, value in branding_data.items():
        if field in allowed_fields:
            settings[field] = value
    
    save_settings(settings)
    return extract_branding_fields(settings)

def update_ai_fields(ai_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update only allowed AI fields, preserving other settings."""
    allowed_fields = {
        "temperature", "top_k", "max_tokens", "strictness", "enableSpeechToText",
        "enableTextToSpeech", "voice", "model", "sttEnabled", "sttLanguage", "sttAutoSend"
    }
    
    settings = load_settings()
    for field, value in ai_data.items():
        if field in allowed_fields:
            settings[field] = value
    
    save_settings(settings)
    return extract_ai_fields(settings)

def update_full_settings(settings_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update complete settings, preserving unlisted fields."""
    settings = load_settings()
    settings.update(settings_data)
    save_settings(settings)
    return extract_full_settings(settings)