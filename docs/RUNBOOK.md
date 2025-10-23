# Lexa AI V2 — Runbook

Complete operational guide for installing, configuring, running, and maintaining Lexa AI V2.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Variables](#environment-variables)
4. [Running the System](#running-the-system)
5. [Health Checks](#health-checks)
6. [Resetting ChromaDB](#resetting-chromadb)
7. [Backup & Restore](#backup--restore)
8. [Maintenance Tasks](#maintenance-tasks)
9. [Upgrading Dependencies](#upgrading-dependencies)

---

## Prerequisites

### Required Versions
- **Python:** 3.12+ (tested with 3.12.3)
- **Node.js:** 18+ (tested with 18.x)
- **Git:** Any recent version

### System Packages (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
  poppler-utils \
  tesseract-ocr \
  ghostscript \
  python3.12 \
  python3.12-venv \
  python3-pip \
  build-essential \
  libpq-dev
```

**Why these packages:**
- `poppler-utils` - PDF rendering for pdf2image
- `tesseract-ocr` - OCR engine for text extraction from images
- `ghostscript` - PDF manipulation for Camelot table extraction
- `build-essential`, `libpq-dev` - Compilation tools for Python packages

### Optional Tools
- **tmux** - For development session management (`./start_lexa.sh`)
- **jq** - JSON formatting for API testing
- **curl** - API health checks

```bash
sudo apt-get install -y tmux jq curl
```

---

## Initial Setup

### 1. Clone Repository

```bash
cd /home/bizbots24/Company_Chatbot_Files
git clone <repository-url> Lexa_AI_V2
cd Lexa_AI_V2
```

### 2. Backend Setup

```bash
# Create Python virtual environment
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should show Python 3.12.x

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Verify installation
python -c "import fastapi, chromadb, openai; print('✅ Core deps OK')"
```

**Expected installation time:** 2-5 minutes depending on network speed

### 3. Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm ci

# Verify installation
npm list --depth=0

# Build for production (optional, for testing)
npm run build
```

**Expected installation time:** 1-3 minutes

### 4. Create Environment Configuration

```bash
# Return to project root
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2

# Create .env file (optional - can also use exported env vars)
cat > backend/.env <<'EOF'
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your-openai-api-key-here

# Admin Access
ADMIN_PASSWORD=Krypt0n!t3
SECRET_KEY=your-secret-key-change-me-to-random-string

# Public Hostname (for production)
PUBLIC_HOST=https://lexaai.bizbots24.com

# Indexing Configuration
LEXA_CHUNK_TOKENS=800
LEXA_EMBED_MODEL=text-embedding-3-large
LEXA_WATCH_DIR=Database
LEXA_OCR_WORD_THRESHOLD=50

# Optional: Disable features
# LEXA_DISABLE_OCR=1
# LEXA_DISABLE_TABLES=1
EOF

# Secure the .env file
chmod 600 backend/.env
```

**⚠️ IMPORTANT:** Never commit `.env` files to git! They are in `.gitignore`.

---

## Environment Variables

### Required Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **YES** | *(none)* | OpenAI API key for embeddings and LLM. Get from https://platform.openai.com/api-keys |

### Security Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADMIN_PASSWORD` | No | `Krypt0n!t3` | Admin panel password. **Change in production!** |
| `SECRET_KEY` | No | `your-secret-key-change-me` | Session signing key. Use random string (32+ chars) |
| `PUBLIC_HOST` | No | *(empty)* | Public-facing URL for file links (e.g., `https://lexaai.bizbots24.com`) |

### Indexing Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEXA_CHUNK_TOKENS` | No | `800` | Target token count per chunk |
| `LEXA_EMBED_MODEL` | No | `text-embedding-3-large` | OpenAI embedding model (also supports `text-embedding-3-small`) |
| `LEXA_WATCH_DIR` | No | `Database` | Directory to monitor for document changes |
| `LEXA_OCR_WORD_THRESHOLD` | No | `50` | Minimum word count before triggering OCR |

### Feature Toggles

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEXA_DISABLE_OCR` | No | *(unset)* | Set to `1` to disable OCR processing |
| `LEXA_DISABLE_TABLES` | No | *(unset)* | Set to `1` to disable table extraction |
| `LEXA_SKIP_IMAGE_ONLY` | No | *(unset)* | Set to `1` to skip image-only PDFs |

### Ollama Configuration (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEXA_ENABLE_OLLAMA` | No | `false` | Enable Ollama local LLM integration |
| `LEXA_OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama API URL |
| `LEXA_OLLAMA_MODEL` | No | `mistral:7b` | Ollama model name |

### Setting Environment Variables

**Method 1: Using .env file (recommended for development)**
```bash
# Edit backend/.env
nano backend/.env

# Source it (optional, python-dotenv loads automatically)
source backend/.env
```

**Method 2: Export in shell (good for testing)**
```bash
export OPENAI_API_KEY="sk-..."
export ADMIN_PASSWORD="MySecurePassword123"
export SECRET_KEY="$(openssl rand -hex 32)"
```

**Method 3: Systemd service (production)**
```bash
# Edit /etc/systemd/system/lexa-backend.service
sudo systemctl edit lexa-backend --full

# Add to [Service] section:
# Environment="OPENAI_API_KEY=sk-..."
# Environment="SECRET_KEY=..."
```

---

## Running the System

### Development Mode (Recommended)

**Option 1: Using tmux launcher (easiest)**

```bash
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2
./start_lexa.sh
```

This script:
- Creates a tmux session named `lexa`
- Window 0: Backend (uvicorn on port 8601)
- Window 1: Frontend (vite dev server on port 8082)
- Window 2: File watcher (auto-reindex on changes)

**Tmux controls:**
- `Ctrl+b` then `0/1/2` - Switch between windows
- `Ctrl+b` then `d` - Detach from session (keeps running)
- `tmux attach -t lexa` - Reattach to session
- `Ctrl+c` in each window - Stop individual services

**Option 2: Manual startup in separate terminals**

Terminal 1 - Backend:
```bash
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2
source .venv/bin/activate
cd backend
uvicorn app:app --host 0.0.0.0 --port 8601 --reload
```

Terminal 2 - Frontend:
```bash
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/frontend
npm run dev
```

Terminal 3 - File Watcher (optional):
```bash
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2
source .venv/bin/activate
cd backend
python -m indexer.watch
```

### Production Mode

**Using systemd services:**

```bash
# Enable and start backend service
sudo systemctl enable lexa-backend
sudo systemctl start lexa-backend

# Enable and start file watcher
sudo systemctl enable ai-bridge-watcher
sudo systemctl start ai-bridge-watcher

# Check status
sudo systemctl status lexa-backend
sudo systemctl status ai-bridge-watcher
```

**Frontend build for production:**
```bash
cd frontend
npm run build

# Serve with nginx, caddy, or similar
# Built files are in frontend/dist/
```

### Stopping the System

**Development (tmux):**
```bash
# Attach to session
tmux attach -t lexa

# Press Ctrl+c in each window (0, 1, 2)
# Then exit tmux: Ctrl+b then type :kill-session
```

**Production (systemd):**
```bash
sudo systemctl stop lexa-backend
sudo systemctl stop ai-bridge-watcher
```

---

## Health Checks

### Backend Health Check

```bash
# Simple check
curl http://localhost:8601/api/health

# Expected response:
# {"status":"ok","service":"lexa-backend"}

# With formatting
curl -s http://localhost:8601/api/health | jq .
```

### Frontend Check

```bash
# Development server
curl http://localhost:8082

# Should return HTML (200 OK)
```

### ChromaDB Check

```bash
source .venv/bin/activate

python -c "
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path='backend/chroma_db',
    settings=Settings(anonymized_telemetry=False)
)

try:
    collection = client.get_collection('lexa_documents')
    count = collection.count()
    print(f'✅ ChromaDB OK - {count} documents indexed')
except Exception as e:
    print(f'❌ ChromaDB error: {e}')
"
```

### Full System Test

```bash
# Test chat endpoint
curl -X GET "http://localhost:8601/api/chat?query=What%20is%20the%20PTO%20policy" \
  -H "Content-Type: application/json" | jq .

# Expected response:
# {
#   "response": "...",
#   "sources": [...]
# }
```

### API Documentation

- **Swagger UI:** http://localhost:8601/api/docs
- **ReDoc:** http://localhost:8601/api/redoc
- **OpenAPI JSON:** http://localhost:8601/api/openapi.json

---

## Resetting ChromaDB

**⚠️ WARNING:** This deletes all indexed documents. You'll need to reindex.

### Safe Reset (Recommended)

```bash
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2

# 1. Stop backend (if running)
# If using tmux: Ctrl+c in backend window
# If using systemd:
sudo systemctl stop lexa-backend

# 2. Backup current database (optional)
mv backend/chroma_db backend/chroma_db.backup.$(date +%Y%m%d_%H%M%S)

# 3. ChromaDB will recreate automatically on next start
# Or manually trigger reindex:
source .venv/bin/activate
cd backend
python -m indexer.reindex Database/

# 4. Restart backend
# Tmux: uvicorn app:app --host 0.0.0.0 --port 8601 --reload
# Systemd: sudo systemctl start lexa-backend
```

### Nuclear Reset (Delete Everything)

```bash
# Stop all services
sudo systemctl stop lexa-backend ai-bridge-watcher

# Delete ChromaDB
rm -rf backend/chroma_db

# Delete cache
rm -rf backend/Database/.lexa-cache

# Delete document mapping
rm -f backend/document_ids.json

# Delete FAQ cache
rm -f backend/data/faq_cache.json

# Reindex from scratch
source .venv/bin/activate
cd backend
python -m indexer.reindex Database/

# Restart services
sudo systemctl start lexa-backend ai-bridge-watcher
```

---

## Backup & Restore

### What to Backup

1. **Vector Database:** `backend/chroma_db/` (~100MB-1GB)
2. **Source Documents:** `backend/Database/` (your PDFs, docs)
3. **Settings:** `backend/storage/settings.json`
4. **Environment:** `backend/.env` (store securely, contains secrets!)

### Backup Script

```bash
#!/bin/bash
# backup_lexa.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/path/to/backups/lexa_backup_${DATE}"
PROJECT_ROOT="/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2"

echo "Creating backup: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Backup vector database
echo "Backing up ChromaDB..."
cp -r "${PROJECT_ROOT}/backend/chroma_db" "${BACKUP_DIR}/"

# Backup source documents
echo "Backing up documents..."
cp -r "${PROJECT_ROOT}/backend/Database" "${BACKUP_DIR}/"

# Backup settings
echo "Backing up settings..."
mkdir -p "${BACKUP_DIR}/storage"
cp "${PROJECT_ROOT}/backend/storage/settings.json" "${BACKUP_DIR}/storage/"

# Backup environment (careful with secrets!)
if [ -f "${PROJECT_ROOT}/backend/.env" ]; then
  echo "Backing up .env (SECURE THIS FILE!)"
  cp "${PROJECT_ROOT}/backend/.env" "${BACKUP_DIR}/"
  chmod 600 "${BACKUP_DIR}/.env"
fi

# Create tarball
echo "Creating tarball..."
cd /path/to/backups
tar -czf "lexa_backup_${DATE}.tar.gz" "lexa_backup_${DATE}"

echo "✅ Backup complete: lexa_backup_${DATE}.tar.gz"
echo "⚠️  Secure this backup - contains API keys!"
```

### Restore from Backup

```bash
#!/bin/bash
# restore_lexa.sh

BACKUP_FILE="$1"  # e.g., lexa_backup_20251022_120000.tar.gz
PROJECT_ROOT="/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file.tar.gz>"
  exit 1
fi

# Stop services
echo "Stopping services..."
sudo systemctl stop lexa-backend ai-bridge-watcher

# Extract backup
echo "Extracting backup..."
tar -xzf "${BACKUP_FILE}"
BACKUP_DIR=$(basename "${BACKUP_FILE}" .tar.gz)

# Restore ChromaDB
echo "Restoring ChromaDB..."
rm -rf "${PROJECT_ROOT}/backend/chroma_db"
cp -r "${BACKUP_DIR}/chroma_db" "${PROJECT_ROOT}/backend/"

# Restore documents
echo "Restoring documents..."
rm -rf "${PROJECT_ROOT}/backend/Database"
cp -r "${BACKUP_DIR}/Database" "${PROJECT_ROOT}/backend/"

# Restore settings
echo "Restoring settings..."
cp "${BACKUP_DIR}/storage/settings.json" "${PROJECT_ROOT}/backend/storage/"

# Restore .env (if exists)
if [ -f "${BACKUP_DIR}/.env" ]; then
  echo "Restoring .env..."
  cp "${BACKUP_DIR}/.env" "${PROJECT_ROOT}/backend/"
  chmod 600 "${PROJECT_ROOT}/backend/.env"
fi

# Restart services
echo "Restarting services..."
sudo systemctl start lexa-backend ai-bridge-watcher

echo "✅ Restore complete!"
```

### Automated Backups (Cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/backup_lexa.sh >> /var/log/lexa_backup.log 2>&1

# Add weekly cleanup (keep last 4 weeks)
0 3 * * 0 find /path/to/backups -name "lexa_backup_*.tar.gz" -mtime +28 -delete
```

---

## Maintenance Tasks

### Reindex Documents

**Full reindex:**
```bash
source .venv/bin/activate
cd backend
python -m indexer.reindex Database/
```

**Reindex specific file:**
```bash
python -m indexer.reindex Database/path/to/file.pdf
```

**Clear cache and reindex:**
```bash
rm -rf Database/.lexa-cache
python -m indexer.reindex Database/
```

### View Indexed Documents

```python
# Run Python shell
source .venv/bin/activate
python

# In Python:
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path='backend/chroma_db',
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection('lexa_documents')

# Get count
print(f"Total documents: {collection.count()}")

# Get sample metadata
results = collection.get(limit=5, include=['metadatas'])
for metadata in results['metadatas']:
    print(f"- {metadata.get('file_name')} (page {metadata.get('page')})")
```

### Clear Logs

**Development:**
```bash
# Logs are in stdout - use tmux scroll buffer or redirect to file
uvicorn app:app --host 0.0.0.0 --port 8601 --reload 2>&1 | tee backend.log
```

**Production (systemd):**
```bash
# View logs
sudo journalctl -u lexa-backend -n 100

# Clear old logs (older than 7 days)
sudo journalctl --vacuum-time=7d
```

### Update Branding

```bash
# Via API (requires admin login)
curl -X POST http://localhost:8601/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"Krypt0n!t3"}' \
  -c cookies.txt

# View current branding
curl -b cookies.txt http://localhost:8601/api/admin/settings/public/branding | jq .

# Or edit directly
nano backend/storage/settings.json
```

---

## Upgrading Dependencies

### Backend Dependencies

```bash
source .venv/bin/activate

# Update all packages
pip install --upgrade -r backend/requirements.txt

# Or update specific package
pip install --upgrade chromadb

# Freeze new versions
pip freeze > backend/requirements.lock

# Test after upgrade
python -c "from backend.lexa_app.retrieval import enhanced_search; print('✅ OK')"
```

### Frontend Dependencies

```bash
cd frontend

# Check for outdated packages
npm outdated

# Update all packages (careful - may break)
npm update

# Update specific package
npm install react@latest

# Rebuild lockfile
npm install

# Test build
npm run build
```

### System Package Updates

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade tesseract-ocr poppler-utils ghostscript
```

---

## Quick Reference

### Essential Commands

```bash
# Start everything (development)
./start_lexa.sh

# Health check
curl http://localhost:8601/api/health

# Reindex documents
source .venv/bin/activate && cd backend && python -m indexer.reindex Database/

# View logs (production)
sudo journalctl -u lexa-backend -f

# Restart backend (production)
sudo systemctl restart lexa-backend

# Backup now
./backup_lexa.sh
```

### Important Paths

```bash
# Project root
/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2

# Backend entry point
backend/app.py

# ChromaDB database
backend/chroma_db/

# Document source
backend/Database/

# Processing cache
backend/Database/.lexa-cache/

# Settings
backend/storage/settings.json

# Virtual environment
.venv/
```

### Default Ports

- **Backend API:** 8601
- **Frontend Dev:** 8082
- **Ollama (if enabled):** 11434

### URLs

- **Frontend:** http://localhost:8082
- **API Docs:** http://localhost:8601/api/docs
- **Admin Panel:** http://localhost:8082/admin/branding
- **Health Check:** http://localhost:8601/api/health

---

## Troubleshooting

For common issues and solutions, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

For system architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md)

For indexing pipeline details, see [INDEXING.md](./INDEXING.md)

For systemd service management, see [SERVICES.md](./SERVICES.md)
