#!/usr/bin/env python3
"""
Rollback tool for Lexa AI settings.
Restores settings from the most recent backup or a specific backup file.
"""

from pathlib import Path
import json
import shutil
from datetime import datetime
from typing import Optional, List
import sys
import argparse
from settings_store import SETTINGS_FILE, STORAGE_DIR

BACKUP_PATTERN = "settings.json.bak.*"

def list_backups() -> List[tuple[str, datetime]]:
    """List all available backup files with timestamps."""
    backups = []
    storage_path = Path(STORAGE_DIR)
    
    for backup_file in storage_path.glob(BACKUP_PATTERN):
        try:
            # Extract timestamp from filename like "settings.json.bak.20250827-234027"
            timestamp_str = backup_file.name.split(".")[-1]  # Get "20250827-234027"
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
            backups.append((str(backup_file), timestamp))
        except ValueError:
            # Skip malformed backup files
            continue
    
    # Sort by timestamp, newest first
    backups.sort(key=lambda x: x[1], reverse=True)
    return backups

def get_latest_backup() -> Optional[Path]:
    """Get the path to the most recent backup file."""
    backups = list_backups()
    if not backups:
        return None
    return Path(backups[0][0])

def preview_backup(backup_path: Path) -> dict:
    """Preview the contents of a backup file."""
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read backup file: {e}")

def rollback_from_backup(backup_path: Path, create_backup: bool = True) -> str:
    """
    Restore settings from a backup file.
    Optionally creates a backup of current settings before rollback.
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Create backup of current state before rollback
    rollback_backup_msg = ""
    if create_backup and SETTINGS_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        rollback_backup_name = f"settings.json.bak.pre-rollback-{timestamp}"
        rollback_backup_path = STORAGE_DIR / rollback_backup_name
        
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SETTINGS_FILE, rollback_backup_path)
        rollback_backup_msg = f"📦 Created pre-rollback backup: {rollback_backup_name}\n"
    
    # Restore from backup
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, SETTINGS_FILE)
    
    # Verify the restore worked
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            restored = json.load(f)
            field_count = len(restored)
    except Exception as e:
        raise RuntimeError(f"Rollback failed - restored file is invalid: {e}")
    
    return f"{rollback_backup_msg}✅ Rolled back to {backup_path.name} ({field_count} fields)"

def main():
    parser = argparse.ArgumentParser(description="Rollback Lexa AI settings from backup")
    parser.add_argument("--list", "-l", action="store_true", 
                       help="List all available backup files")
    parser.add_argument("--backup", "-b", type=str, 
                       help="Specific backup file to restore from")
    parser.add_argument("--latest", action="store_true", 
                       help="Restore from the most recent backup")
    parser.add_argument("--preview", "-p", type=str, 
                       help="Preview contents of a backup file")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip creating backup of current settings before rollback")
    
    args = parser.parse_args()
    
    try:
        if args.list:
            print("📋 Available backup files:")
            backups = list_backups()
            if not backups:
                print("   No backup files found.")
                return
            
            for i, (backup_path, timestamp) in enumerate(backups):
                backup_name = Path(backup_path).name
                age = datetime.now() - timestamp
                print(f"   {i+1}. {backup_name} ({timestamp.strftime('%Y-%m-%d %H:%M:%S')}, {age.days} days ago)")
            return
        
        if args.preview:
            backup_path = Path(STORAGE_DIR) / args.preview if not args.preview.startswith('/') else Path(args.preview)
            if not backup_path.exists():
                backup_path = Path(args.preview)
            
            data = preview_backup(backup_path)
            print(f"📄 Preview of {backup_path.name}:")
            print(f"   Fields: {len(data)}")
            
            # Show key fields
            key_fields = ["companyName", "model", "temperature", "max_tokens"]
            for field in key_fields:
                if field in data:
                    print(f"   {field}: {data[field]}")
            return
        
        if args.latest:
            backup_path = get_latest_backup()
            if not backup_path:
                print("❌ No backup files found.")
                sys.exit(1)
        elif args.backup:
            backup_path = Path(STORAGE_DIR) / args.backup if not args.backup.startswith('/') else Path(args.backup)
            if not backup_path.exists():
                backup_path = Path(args.backup)
        else:
            print("❌ Must specify --latest, --backup, --list, or --preview")
            parser.print_help()
            sys.exit(1)
        
        # Confirm rollback
        if not args.preview and not args.list:
            print(f"⚠️  About to rollback from: {backup_path.name}")
            response = input("Continue? (y/N): ").strip().lower()
            if response != 'y':
                print("🚫 Rollback cancelled.")
                return
            
            result = rollback_from_backup(backup_path, create_backup=not args.no_backup)
            print(result)
            print("🎉 Rollback complete!")
            
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()