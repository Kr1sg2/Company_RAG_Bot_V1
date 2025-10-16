#!/usr/bin/env bash
set -euo pipefail
INBOX="$HOME/ai-bridge/inbox"
REPO_ROOT="${1:-$PWD}"

echo "[*] Watching $INBOX for *.diff … (Ctrl+C to stop)"
inotifywait -m -e close_write --format '%w%f' "$INBOX" | while read -r file; do
  if [[ "$file" == *.diff || "$file" == *.patch ]]; then
    echo "[*] Detected patch: $file"
    "$HOME/ai-bridge/bin/apply_and_test.sh" "$file" "$REPO_ROOT" || true
  fi
done
