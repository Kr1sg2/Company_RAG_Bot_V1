#!/bin/bash
# clean_chroma.sh - Clean ChromaDB and cache for fresh start

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/Backend_FastAPI"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Lexa AI - Clean Database & Cache${NC}"
echo "================================================="

# Change to backend directory
cd "$BACKEND_DIR"

# Get configured paths
CHROMA_PATH="${LEXA_CHROMA_PATH:-chroma_db}"
CACHE_DIR="${LEXA_CACHE_DIR:-Database/.lexa-cache}"

echo -e "${BLUE}📍 Paths to clean:${NC}"
echo "ChromaDB: $CHROMA_PATH"
echo "Cache: $CACHE_DIR"
echo ""

# Confirmation
echo -e "${YELLOW}⚠️  This will permanently delete all indexed data and cache!${NC}"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Clean cancelled."
    exit 0
fi

# Stop services if running
echo -e "${YELLOW}🛑 Stopping services...${NC}"
if pgrep -f "uvicorn.*app:app" > /dev/null; then
    echo "Stopping backend service..."
    pkill -f "uvicorn.*app:app" || true
    sleep 2
fi

if pgrep -f "indexer.watch" > /dev/null; then
    echo "Stopping indexer service..."
    pkill -f "indexer.watch" || true
    sleep 2
fi

# Clean ChromaDB
if [ -d "$CHROMA_PATH" ]; then
    echo -e "${YELLOW}🗑️  Removing ChromaDB: $CHROMA_PATH${NC}"
    rm -rf "$CHROMA_PATH"
    echo "✅ ChromaDB deleted"
else
    echo "ℹ️  ChromaDB directory not found: $CHROMA_PATH"
fi

# Clean cache
if [ -d "$CACHE_DIR" ]; then
    echo -e "${YELLOW}🗑️  Removing cache: $CACHE_DIR${NC}"
    rm -rf "$CACHE_DIR"
    echo "✅ Cache deleted"
else
    echo "ℹ️  Cache directory not found: $CACHE_DIR"
fi

# Clean any log files
if [ -f "backend.log" ]; then
    echo -e "${YELLOW}🗑️  Clearing log files...${NC}"
    > backend.log
    echo "✅ Logs cleared"
fi

# Clean Python cache
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo -e "${GREEN}✅ Cleanup completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart services: ./start_lexa.sh"
echo "2. Or reindex manually: ./scripts/reindex.sh"