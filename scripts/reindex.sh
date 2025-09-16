#!/bin/bash
# reindex.sh - Rebuild the entire document index

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

echo -e "${BLUE}🔄 Lexa AI - Full Document Reindex${NC}"
echo "================================================="

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    echo -e "${RED}❌ Virtual environment not found in $BACKEND_DIR/.venv${NC}"
    echo "Run setup first: cd $BACKEND_DIR && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment
source .venv/bin/activate

# Check if required packages are installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
python -c "import openai, chromadb" 2>/dev/null || {
    echo -e "${RED}❌ Required packages not installed${NC}"
    echo "Install with: pip install -r requirements.txt"
    exit 1
}

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY environment variable not set${NC}"
    echo "Please set it before running reindex:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# Configuration info
echo -e "${BLUE}⚙️  Current Configuration:${NC}"
echo "Watch Directory: ${LEXA_WATCH_DIR:-Database}"
echo "Cache Directory: ${LEXA_CACHE_DIR:-Database/.lexa-cache}"
echo "Chunk Size: ${LEXA_CHUNK_CHARS:-1200} characters"
echo "Chunk Overlap: ${LEXA_CHUNK_OVERLAP:-0.25} (25%)"
echo "OCR Disabled: ${LEXA_DISABLE_OCR:-0}"
echo "Tables Disabled: ${LEXA_DISABLE_TABLES:-0}"
echo "Skip Image-Only: ${LEXA_SKIP_IMAGE_ONLY:-0}"
echo ""

# Confirmation
read -p "Continue with reindex? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Reindex cancelled."
    exit 0
fi

# Clear ChromaDB
echo -e "${YELLOW}🗑️  Clearing existing ChromaDB...${NC}"
if [ -d "chroma_db" ]; then
    rm -rf chroma_db
    echo "Deleted existing ChromaDB"
fi

# Clear cache
echo -e "${YELLOW}🗑️  Clearing cache...${NC}"
CACHE_DIR="${LEXA_CACHE_DIR:-Database/.lexa-cache}"
if [ -d "$CACHE_DIR" ]; then
    rm -rf "$CACHE_DIR"
    echo "Deleted existing cache"
fi

# Start reindexing
echo -e "${GREEN}🚀 Starting reindex...${NC}"
WATCH_DIR="${LEXA_WATCH_DIR:-Database}"

if [ ! -d "$WATCH_DIR" ]; then
    echo -e "${RED}❌ Watch directory not found: $WATCH_DIR${NC}"
    exit 1
fi

# Count files to process
FILE_COUNT=$(find "$WATCH_DIR" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.txt" -o -name "*.md" -o -name "*.rtf" -o -name "*.xlsx" -o -name "*.xls" -o -name "*.csv" -o -name "*.pptx" -o -name "*.ppt" \) | wc -l)
echo "Found $FILE_COUNT documents to process"

# Run the reindexing
python -c "
import sys
sys.path.append('.')
from indexer.reindex import reindex_all
reindex_all('$WATCH_DIR')
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Reindex completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start the backend: uvicorn app:app --host 0.0.0.0 --port 8601"
    echo "2. Test with: curl 'http://localhost:8601/api/chat/?query=test'"
else
    echo -e "${RED}❌ Reindex failed!${NC}"
    echo "Check the logs above for error details."
    exit 1
fi