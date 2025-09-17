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


def _get_nested(d: Dict[str, Any], path: str, default=None):
    cur = d or {}
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def extract_branding_fields(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only branding-related fields with defaults."""
    # Nested, legacy-compatible sources (will be used as fallbacks for flat keys)
    nested_colors = settings.get("colors", {})
    nested_bubbles = settings.get("bubbles", {})

    branding = {
        # Basic Settings
        "companyName": settings.get("companyName", "Leaders AI Company Chatbot"),
        "taglineText": settings.get(
            "taglineText",
            "Closed-book RAG system - answers only from company documents",
        ),
        "emptyStateText": settings.get(
            "emptyStateText", "Ask me anything about your company documents!"
        ),
        "inputPlaceholder": settings.get(
            "inputPlaceholder", "Ask a question about your documents..."
        ),
        "logoDataUrl": settings.get("logoDataUrl"),
        "faviconUrl": settings.get("faviconUrl"),
        # Background images (page/card)
        "pageBackgroundUrl": settings.get("pageBackgroundUrl"),
        "chatCardBackgroundUrl": settings.get("chatCardBackgroundUrl"),
        # Keep legacy nested objects
        "colors": settings.get(
            "colors",
            {
                "primary": "#6190ff",
                "accent": "#756bff",
                "bg": "#0b1020",
                "text": "#e6e6e6",
            },
        ),
        "bubbles": settings.get(
            "bubbles", {"radius": "18px", "aiBg": "#0f1530", "userBg": "#1b2447"}
        ),
        # Original dimensions / legacy
        "chatWidth": settings.get("chatWidth", "920"),
        "chatHeight": settings.get("chatHeight", "56"),
        "chatOffsetTop": settings.get("chatOffsetTop", "7"),
        "cardRadius": settings.get("cardRadius", "18"),
        "cardBg": settings.get("cardBg", "rgba(255,255,255,0.88)"),
        # Typography
        "fontFamily": settings.get("fontFamily", "system-ui"),
        "titleFontSize": settings.get("titleFontSize", 32),
        "bodyFontSize": settings.get("bodyFontSize", 16),
        "titleBold": settings.get("titleBold", True),
        "titleItalic": settings.get("titleItalic", False),
        "taglineFontSize": settings.get("taglineFontSize", 18),
        "taglineBold": settings.get("taglineBold", False),
        "taglineItalic": settings.get("taglineItalic", False),
        # Enhanced Bubble Controls
        "bubblePadding": settings.get("bubblePadding", 12),
        "bubbleMaxWidth": settings.get("bubbleMaxWidth", 70),
        "aiTextColor": settings.get("aiTextColor", "#121212"),
        "aiBubbleBorder": settings.get("aiBubbleBorder", "none"),
        "userTextColor": settings.get("userTextColor", "#111111"),
        "userBubbleBorder": settings.get("userBubbleBorder", "none"),
        # Enhanced Card Controls
        "cardPadding": settings.get("cardPadding", 24),
        "inputHeight": settings.get("inputHeight", 44),
        "inputRadius": settings.get("inputRadius", 8),
        "messageSpacing": settings.get("messageSpacing", 16),
        # Backgrounds & Shadows
        "pageBackgroundColor": settings.get("pageBackgroundColor", "#ffffff"),
        "cardBackgroundColor": settings.get("cardBackgroundColor", "#ffffff"),
        "cardOpacity": settings.get("cardOpacity", 100),
        "shadowColor": settings.get("shadowColor", "#000000"),
        "shadowBlur": settings.get("shadowBlur", 10),
        "shadowSpread": settings.get("shadowSpread", 0),
        "shadowOpacity": settings.get("shadowOpacity", 20),
        "enableShadow": settings.get("enableShadow", True),
        "enableGlow": settings.get("enableGlow", False),
        # Robot / Avatar
        "avatarImageUrl": settings.get("avatarImageUrl"),
        "avatarSize": settings.get("avatarSize", 40),
        "avatarPosition": settings.get("avatarPosition", "left"),
        "avatarShape": settings.get("avatarShape", "circle"),
        "showAvatarOnMobile": settings.get("showAvatarOnMobile", True),
        # User Avatar
        "userAvatarImageUrl": settings.get("userAvatarImageUrl"),
        "userAvatarSize": settings.get("userAvatarSize", 40),
        "userAvatarPosition": settings.get("userAvatarPosition", "right"),
        "userAvatarShape": settings.get("userAvatarShape", "circle"),
        "showUserAvatarOnMobile": settings.get("showUserAvatarOnMobile", True),
        # Audio / TTS & STT
        "enableTextToSpeech": settings.get("enableTextToSpeech", False),
        "enableSpeechToText": settings.get("enableSpeechToText", False),
        "ttsVoice": settings.get("ttsVoice", "default"),
        "ttsSpeed": settings.get("ttsSpeed", 1.0),
        "sttLanguage": settings.get("sttLanguage", "en-US"),
        "sttAutoSend": settings.get("sttAutoSend", False),
        "showAudioControls": settings.get("showAudioControls", True),
        "ttsAutoPlay": settings.get("ttsAutoPlay", False),
        # LLM Controls
        "aiModel": settings.get("aiModel", "gpt-4"),
        "aiTemperature": settings.get("aiTemperature", 0.7),
        "aiMaxTokens": settings.get("aiMaxTokens", 2048),
        "aiTopK": settings.get("aiTopK", 50),
        "aiStrictness": settings.get("aiStrictness", "balanced"),
        "aiSystemPrompt": settings.get(
            "aiSystemPrompt", "You are a helpful AI assistant."
        ),
        "aiStreamResponses": settings.get("aiStreamResponses", True),
        "aiRetainContext": settings.get("aiRetainContext", True),
        "aiResponseStyle": settings.get("aiResponseStyle", "auto"),
        # -------- NEW: flat keys expected by Admin/Chat --------
        # Theme colors (flat) with fallbacks to nested
        "primaryColor": settings.get(
            "primaryColor", nested_colors.get("primary", "#6190ff")
        ),
        "accentColor": settings.get(
            "accentColor", nested_colors.get("accent", "#756bff")
        ),
        "textColor": settings.get("textColor", nested_colors.get("text", "#e6e6e6")),
        "mutedTextColor": settings.get("mutedTextColor", "#64748b"),
        "titleColor": settings.get(
            "titleColor",
            settings.get("textColor", nested_colors.get("text", "#0f172a")),
        ),
        "taglineColor": settings.get(
            "taglineColor", settings.get("mutedTextColor", "#64748b")
        ),
        # Inputs & buttons (flat)
        "inputBackgroundColor": settings.get("inputBackgroundColor", "#ffffff"),
        "inputTextColor": settings.get("inputTextColor", "#0f172a"),
        "sendButtonBgColor": settings.get(
            "sendButtonBgColor",
            settings.get("primaryColor", nested_colors.get("primary", "#6190ff")),
        ),
        "sendButtonTextColor": settings.get("sendButtonTextColor", "#ffffff"),
        "sendBtnText": settings.get("sendBtnText", "Send"),
        # Bubble specifics (flat) with fallbacks to nested bubbles
        "bubbleRadius": settings.get(
            "bubbleRadius", nested_bubbles.get("radius", "18px")
        ),
        "aiBubbleBg": settings.get("aiBubbleBg", nested_bubbles.get("aiBg", "#0f1530")),
        "userBubbleBg": settings.get(
            "userBubbleBg", nested_bubbles.get("userBg", "#1b2447")
        ),
        "assistantBold": settings.get("assistantBold", False),
        "assistantItalic": settings.get("assistantItalic", False),
        "userBold": settings.get("userBold", False),
        "userItalic": settings.get("userItalic", False),
        # NEW: Bubble opacity controls (0.0-1.0)
        "aiOpacity": settings.get("aiOpacity"),
        "userOpacity": settings.get("userOpacity"),
        "aiBorderColor": settings.get("aiBorderColor"),
        "userBorderColor": settings.get("userBorderColor"),
        "aiBorderWidth": settings.get("aiBorderWidth"),
        "userBorderWidth": settings.get("userBorderWidth"),
        # Test probe
        "__persist_probe": settings.get("__persist_probe"),
        # Card background advanced
        "cardBackgroundUrl": settings.get("cardBackgroundUrl"),
        "cardBackgroundCssOverride": settings.get("cardBackgroundCssOverride"),
        # Glow (flat)
        "glowColor": settings.get(
            "glowColor",
            settings.get("primaryColor", nested_colors.get("primary", "#6190ff")),
        ),
        "glowBlur": settings.get("glowBlur", 25),
        "glowOpacity": settings.get("glowOpacity", 20),
    }

    # Remove None values
    return {k: v for k, v in branding.items() if v is not None}


def _coerce_float(v, dflt):
    try:
        return float(v)
    except Exception:
        return dflt


def _coerce_int(v, dflt):
    try:
        return int(v)
    except Exception:
        return dflt


def _clamp(v, lo, hi, default):
    try:
        x = float(v)
    except Exception:
        return default
    return max(lo, min(hi, x))


def extract_ai_fields(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return AI config with canonical keys used by the OpenAI call.
    Accept both old and new admin keys and clamp to safe ranges.
    """
    s = settings or {}
    # Accept multiple spellings; prefer canonical if present
    model = s.get("model") or s.get("aiModel") or s.get("openaiModel") or "gpt-4o-mini"
    temperature = _clamp(
        s.get("temperature", s.get("aiTemperature", 0.7)), 0.0, 2.0, 0.7
    )
    max_tokens = int(
        _clamp(s.get("max_tokens", s.get("aiMaxTokens", 900)), 1, 4000, 900)
    )
    top_p = _clamp(s.get("top_p", 1.0), 0.0, 1.0, 1.0)
    frequency_penalty = _clamp(s.get("frequency_penalty", 0.0), -2.0, 2.0, 0.0)
    presence_penalty = _clamp(s.get("presence_penalty", 0.0), -2.0, 2.0, 0.0)

    # Optional helpers
    strictness = int(_clamp(s.get("strictness", 4), 0, 10, 4))
    system_prompt = s.get("systemPrompt") or ""

    return {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "top_p": float(top_p),
        "frequency_penalty": float(frequency_penalty),
        "presence_penalty": float(presence_penalty),
        "strictness": strictness,
        "systemPrompt": system_prompt,
    }


def extract_full_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Extract complete settings (merge branding + AI)."""
    full = {}
    full.update(extract_branding_fields(settings))
    full.update(extract_ai_fields(settings))
    return full


def update_branding_fields(branding_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update branding fields, preserving other settings. Block only sensitive fields."""
    # Block sensitive/auth fields but allow all branding-related fields
    blocked_fields = {
        "openaiApiKey",
        "adminPassword",
        "secretKey",
        "sessionSecret",
        "databaseUrl",
        "apiKeys",
        "credentials",
        "password",
        "token",
        "auth",
        "secret",
        "key",  # generic patterns
    }

    settings = load_settings()
    for field, value in branding_data.items():
        # Allow the field unless it contains blocked patterns
        field_lower = field.lower()
        if not any(blocked in field_lower for blocked in blocked_fields):
            settings[field] = value

    save_settings(settings)
    return extract_branding_fields(settings)


def update_ai_fields(ai_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update only allowed AI fields, preserving other settings."""
    allowed_fields = {
        "temperature",
        "top_k",
        "max_tokens",
        "strictness",
        "enableSpeechToText",
        "enableTextToSpeech",
        "voice",
        "model",
        "sttEnabled",
        "sttLanguage",
        "sttAutoSend",
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
