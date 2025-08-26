#!/usr/bin/env bash
set -euo pipefail
REPO="/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2"
BACK="$REPO/Backend_FastAPI"
FRONT="$REPO/Frontend_Client_Side"
LOGS="$REPO/.agent_logs"
mkdir -p "$LOGS"

# free ports
for P in 8600 8080; do
  pids=$(lsof -ti tcp:$P || true)
  [ -n "$pids" ] && kill -9 $pids || true
done

# backend
cd "$BACK"
test -d .venv || python3 -m venv .venv
source .venv/bin/activate
pip install -q --disable-pip-version-check fastapi uvicorn || true
nohup uvicorn app:app --host 0.0.0.0 --port 8600 --log-level info > "$LOGS/backend.log" 2>&1 &
echo $! > "$LOGS/backend.pid"

# frontend (HTTP on 8080)
cd "$FRONT"
npm install --silent >/dev/null 2>&1 || true
nohup npm run dev -- --host --port 8080 > "$LOGS/frontend.log" 2>&1 &
echo $! > "$LOGS/frontend.pid"

# quick health probes
sleep 1
echo "[start_all] backend health:";  curl -fsS http://127.0.0.1:8600/health | head -c 200 || echo "not ready"
echo
echo "[start_all] frontend:";       curl -fsS http://127.0.0.1:8080        | head -c 200 || echo "not ready"
echo
echo "PIDs: backend=$(cat "$LOGS/backend.pid") frontend=$(cat "$LOGS/frontend.pid")"
echo "Logs: $LOGS/backend.log  |  $LOGS/frontend.log"
