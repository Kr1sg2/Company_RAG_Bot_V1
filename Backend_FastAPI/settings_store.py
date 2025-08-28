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
        "companyName": settings.get("companyName", "Leaders AI Company Chatbot"),
        "taglineText": settings.get("taglineText", "Closed-book RAG system - answers only from company documents"),
        "emptyStateText": settings.get("emptyStateText", "Ask me anything about your company documents!"),
        "inputPlaceholder": settings.get("inputPlaceholder", "Ask a question about your documents..."),
        "logoDataUrl": settings.get("logoDataUrl"),
        "faviconUrl": settings.get("faviconUrl"),
        "pageBackgroundUrl": settings.get("pageBackgroundUrl"),
        "chatCardBackgroundUrl": settings.get("chatCardBackgroundUrl"),
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
        "chatWidth": settings.get("chatWidth", "920"),
        "chatHeight": settings.get("chatHeight", "56"),
        "chatOffsetTop": settings.get("chatOffsetTop", "7"),
        "cardRadius": settings.get("cardRadius", "18"),
        "cardBg": settings.get("cardBg", "rgba(255,255,255,0.88)")
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
        "companyName", "taglineText", "emptyStateText", "inputPlaceholder",
        "logoDataUrl", "faviconUrl", "pageBackgroundUrl", "chatCardBackgroundUrl",
        "colors", "bubbles", "chatWidth", "chatHeight", "chatOffsetTop", 
        "cardRadius", "cardBg"
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