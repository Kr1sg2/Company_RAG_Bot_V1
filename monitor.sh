#!/bin/bash

for i in {1..20}; do
  echo "--- poll $i ---"
  BACK=$(curl -sS http://127.0.0.1:8600/health || echo FAIL)
  FRONT=$(curl -sI http://127.0.0.1:8080 2>/dev/null | head -n1 || echo FAIL)
  echo "backend: $BACK"
  echo "frontend: $FRONT"
  
  if ! echo "$BACK" | grep -q '"ok":true'; then
    echo "backend down -> restarting"
    bash /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/start_backend.sh
  fi
  
  if ! echo "$FRONT" | grep -q "200"; then
    echo "frontend down -> restarting"
    bash /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/start_frontend.sh
  fi
  
  sleep 30
done