#!/usr/bin/env bash
set -euo pipefail
REPO="/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2"
LOGS="$REPO/.agent_logs"
for f in "$LOGS/backend.pid" "$LOGS/frontend.pid"; do
  if [ -f "$f" ]; then pid=$(cat "$f"); kill -9 "$pid" 2>/dev/null || true; rm -f "$f"; fi
done
pkill -f "uvicorn app:app" 2>/dev/null || true
pkill -f "python3 -m uvicorn" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "node .*dev" 2>/dev/null || true
echo "[stop_all] stopped"
