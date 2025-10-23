#!/usr/bin/env bash
# AI Bridge Workspace Cleanup Script
# Generated: 2025-10-15
# Purpose: Remove temporary files, old backups, and test artifacts safely

set -euo pipefail

REPO_ROOT="/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2"
BACKEND_DIR="$REPO_ROOT/backend"
AIBRIDGE_DIR="/home/bizbots24/ai-bridge/inbox"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[CLEAN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Track what we cleaned
CLEANED_FILES=0
CLEANED_SIZE=0

cleanup_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        local size
        size=$(stat -c '%s' "$file" 2>/dev/null || echo 0)
        rm -f "$file"
        log "Removed file: $file (${size} bytes)"
        CLEANED_FILES=$((CLEANED_FILES + 1))
        CLEANED_SIZE=$((CLEANED_SIZE + size))
    fi
}

cleanup_dir() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        local size
        size=$(du -sb "$dir" 2>/dev/null | cut -f1 || echo 0)
        rm -rf "$dir"
        log "Removed directory: $dir (${size} bytes)"
        CLEANED_FILES=$((CLEANED_FILES + 1))
        CLEANED_SIZE=$((CLEANED_SIZE + size))
    fi
}

echo "=================================================="
echo "🧹 AI Bridge Workspace Cleanup Script"
echo "=================================================="
log "Starting cleanup in: $REPO_ROOT"

# 1. Remove untracked orphaned files
log "Cleaning untracked files..."
cleanup_file "$REPO_ROOT/=4.0.0"

# 2. Clean old app.py backup files (keep only the 2 most recent)
log "Cleaning old app.py backup files..."
cd "$BACKEND_DIR"
# Get list of backup files sorted by modification time (oldest first)
mapfile -t backup_files < <(find . -name "app.py.bak.*" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | cut -d' ' -f2-)

if [[ ${#backup_files[@]} -gt 2 ]]; then
    # Remove all but the last 2 (most recent)
    for ((i=0; i<${#backup_files[@]}-2; i++)); do
        cleanup_file "$BACKEND_DIR/${backup_files[$i]#./}"
    done
else
    log "Only ${#backup_files[@]} app.py backup files found, keeping all"
fi

# 3. Clean settings backup files
log "Cleaning settings backup files..."
for file in "$BACKEND_DIR"/settings_store.py.bak.*; do
    [[ -f "$file" ]] && cleanup_file "$file"
done

# 4. Remove old indexer backup directory
log "Cleaning old indexer backup directory..."
cleanup_dir "$BACKEND_DIR/indexer.bak.1757152123"

# 5. Clean old log files (>30 days)
log "Cleaning old log files (>30 days)..."
find "$REPO_ROOT" -name "*.log" -type f -mtime +30 -print0 2>/dev/null | while IFS= read -r -d '' file; do
    cleanup_file "$file"
done

# 6. Clean AI-Bridge test files we created during testing
log "Cleaning AI-Bridge test files..."
if [[ -d "$AIBRIDGE_DIR/.processed" ]]; then
    find "$AIBRIDGE_DIR/.processed" -name "test_safe.diff" -type f -exec rm -f {} \; 2>/dev/null || true
    find "$AIBRIDGE_DIR/.processed" -name "test.json" -type f -exec rm -f {} \; 2>/dev/null || true  
    find "$AIBRIDGE_DIR/.processed" -name "test.txt" -type f -exec rm -f {} \; 2>/dev/null || true
    log "Removed AI-Bridge test files from processed directory"
fi

# Clean any remaining test files in inbox
[[ -f "$AIBRIDGE_DIR/test.exe" ]] && cleanup_file "$AIBRIDGE_DIR/test.exe"

# 7. Clean empty directories in processed folder
log "Cleaning empty processed directories..."
if [[ -d "$AIBRIDGE_DIR/.processed" ]]; then
    find "$AIBRIDGE_DIR/.processed" -type d -empty -delete 2>/dev/null || true
    log "Removed empty directories from processed folder"
fi

# 8. Clean Python cache files (if any appear)
log "Cleaning Python cache files..."
find "$REPO_ROOT" \( -name "__pycache__" -type d -exec rm -rf {} + \) -o \
                 \( -name "*.pyc" -delete \) -o \
                 \( -name "*.pyo" -delete \) 2>/dev/null || true

# 9. Clean editor temporary files
log "Cleaning editor temporary files..."
find "$REPO_ROOT" \( -name "*~" -delete \) -o \
                 \( -name "*.swp" -delete \) -o \
                 \( -name ".DS_Store" -delete \) 2>/dev/null || true

echo "=================================================="
success "Cleanup completed!"
log "Files/directories cleaned: $CLEANED_FILES"
log "Total space recovered: $CLEANED_SIZE bytes ($(( CLEANED_SIZE / 1024 ))KB)"

# Optional: Show remaining backup files for review
echo ""
log "Remaining backup files (kept for safety):"
find "$BACKEND_DIR" -name "*.bak*" -o -name "*backup*" | sort | while read -r file; do
    if [[ -f "$file" ]]; then
        size=$(stat -c '%s' "$file")
        echo "  📁 $file (${size} bytes)"
    fi
done

echo ""
success "Workspace cleanup complete! 🎉"
log "Repository is now cleaner and ready for development"