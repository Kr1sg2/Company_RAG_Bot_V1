# AI Bridge Watcher (Bash)

This is the production watcher currently in use. It uses `inotifywait` to watch an inbox directory for new files (e.g., `.diff`, `.patch`, `.json`) and then performs actions (archive, forward, etc.)

## Environment (via `/etc/lexa/ai-bridge.env`)


> Adjust extensions/URL to your needs.

## Dependencies
- `inotifywait` from `inotify-tools` package
- bash

Install:
sudo apt-get update
sudo apt-get install -y inotify-tools
