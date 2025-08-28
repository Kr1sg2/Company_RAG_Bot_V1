#!/usr/bin/env python3
"""
Settings migration tool for Lexa AI backend.
Backs up existing settings and ensures all required fields exist with defaults.
"""

from pathlib import Path
import json
import shutil
from datetime import datetime
from typing import Dict, Any
from settings_store import load_settings, save_settings, extract_branding_fields, extract_ai_fields

SETTINGS_FILE = Path("storage/settings.json")
STORAGE_DIR = Path("storage")

def backup_existing_settings() -> str:
    """Create timestamped backup of existing settings.json if it exists."""
    if not SETTINGS_FILE.exists():
        return "No existing settings file to backup"
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"settings.json.bak.{timestamp}"
    backup_path = STORAGE_DIR / backup_name
    
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SETTINGS_FILE, backup_path)
    
    return f"Backed up settings to {backup_name}"

def migrate_once() -> Dict[str, Any]:
    """
    Ensure all required settings fields exist with defaults.
    Does not overwrite existing values.
    """
    print("Starting settings migration...")
    
    # Backup existing file
    backup_msg = backup_existing_settings()
    print(f"📦 {backup_msg}")
    
    # Load current settings (or empty dict)
    current_settings = load_settings()
    print(f"📊 Loaded {len(current_settings)} existing settings")
    
    # Get all required defaults
    branding_defaults = extract_branding_fields({})  # Empty dict gets pure defaults
    ai_defaults = extract_ai_fields({})  # Empty dict gets pure defaults
    
    all_defaults = {**branding_defaults, **ai_defaults}
    
    # Track what we're adding
    added_fields = []
    updated_settings = current_settings.copy()
    
    for field, default_value in all_defaults.items():
        if field not in updated_settings:
            updated_settings[field] = default_value
            added_fields.append(f"{field}={default_value}")
    
    if added_fields:
        print(f"✨ Adding {len(added_fields)} missing fields:")
        for field in added_fields:
            print(f"   + {field}")
        
        save_settings(updated_settings)
        print(f"💾 Saved settings with {len(updated_settings)} total fields")
    else:
        print("✅ All required fields already exist - no migration needed")
    
    return updated_settings

if __name__ == "__main__":
    try:
        result = migrate_once()
        print(f"\n🎉 Migration complete! Settings file has {len(result)} fields total.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise