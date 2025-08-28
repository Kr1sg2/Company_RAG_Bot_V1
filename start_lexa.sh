#!/bin/bash

# Lexa AI Development Environment Launcher
# Usage: ./start_lexa.sh
# 
# This script launches:
# - Backend FastAPI server on port 8600
# - Frontend Vite dev server on port 8080 with proxy to backend
#
# Requirements:
# - tmux installed
# - Backend Python virtual environment set up
# - Frontend node_modules installed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/Backend_FastAPI"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo -e "${BLUE}🚀 Lexa AI Development Environment Launcher${NC}"
echo "================================================="
echo ""

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}❌ Error: tmux is required but not installed${NC}"
    echo "Install with: sudo apt-get install tmux (Ubuntu/Debian) or brew install tmux (macOS)"
    exit 1
fi

# Check if session already exists
if tmux has-session -t lexa-dev 2>/dev/null; then
    echo -e "${YELLOW}⚠️  tmux session 'lexa-dev' already exists${NC}"
    echo "Options:"
    echo "  1. Attach to existing session: tmux attach -t lexa-dev"
    echo "  2. Kill existing session and restart: tmux kill-session -t lexa-dev && ./start_lexa.sh"
    exit 1
fi

# Verify directories exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

# Check backend virtual environment
if [ ! -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    echo -e "${RED}❌ Backend virtual environment not found${NC}"
    echo "Create it with: cd $BACKEND_DIR && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check frontend node_modules
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${RED}❌ Frontend node_modules not found${NC}"
    echo "Install dependencies with: cd $FRONTEND_DIR && npm install"
    exit 1
fi

echo -e "${GREEN}✅ Pre-flight checks passed${NC}"
echo ""

# Create tmux session
echo -e "${BLUE}📦 Creating tmux session 'lexa-dev'...${NC}"
tmux new-session -d -s lexa-dev -c "$SCRIPT_DIR"

# Setup backend window
echo -e "${BLUE}🔧 Setting up backend server (port 8600)...${NC}"
tmux rename-window -t lexa-dev:0 'backend'
tmux send-keys -t lexa-dev:backend "cd '$BACKEND_DIR'" Enter
tmux send-keys -t lexa-dev:backend "source .venv/bin/activate" Enter
tmux send-keys -t lexa-dev:backend "uvicorn app:app --reload --host 0.0.0.0 --port 8600" Enter

# Create frontend window
echo -e "${BLUE}🎨 Setting up frontend server (port 8080)...${NC}"
tmux new-window -t lexa-dev -n 'frontend' -c "$FRONTEND_DIR"
tmux send-keys -t lexa-dev:frontend "npm run dev" Enter

# Create logs window
tmux new-window -t lexa-dev -n 'logs' -c "$SCRIPT_DIR"
tmux send-keys -t lexa-dev:logs "echo 'Logs window - use this for debugging'" Enter
tmux send-keys -t lexa-dev:logs "echo 'Backend logs: tmux capture-pane -t lexa-dev:backend -p'" Enter
tmux send-keys -t lexa-dev:logs "echo 'Frontend logs: tmux capture-pane -t lexa-dev:frontend -p'" Enter

# Switch to backend window to show startup
tmux select-window -t lexa-dev:backend

# Wait a moment for servers to start
sleep 2

echo ""
echo -e "${GREEN}🎉 Lexa AI Development Environment Started!${NC}"
echo "================================================="
echo -e "🔗 Frontend: ${BLUE}http://localhost:8080${NC}"
echo -e "🔗 Backend API: ${BLUE}http://localhost:8600${NC}"
echo -e "🔗 Admin Panel: ${BLUE}http://localhost:8080/admin${NC}"
echo ""
echo -e "${YELLOW}tmux Commands:${NC}"
echo "  • Attach to session:    tmux attach -t lexa-dev"
echo "  • Switch windows:       Ctrl+b then 0/1/2 (backend/frontend/logs)"
echo "  • Detach from session:  Ctrl+b then d"
echo "  • Kill session:         tmux kill-session -t lexa-dev"
echo ""
echo -e "${BLUE}Starting tmux session...${NC}"

# Attach to the session
tmux attach -t lexa-dev