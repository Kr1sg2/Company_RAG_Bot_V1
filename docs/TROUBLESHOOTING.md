# Lexa AI V2 — Troubleshooting Guide

Comprehensive troubleshooting guide with precise solutions for common issues.

---

## Table of Contents

1. [Backend Issues](#backend-issues)
2. [Frontend Issues](#frontend-issues)
3. [Indexing & Document Processing](#indexing--document-processing)
4. [ChromaDB & Vector Search](#chromadb--vector-search)
5. [Authentication & Sessions](#authentication--sessions)
6. [API & Network Issues](#api--network-issues)
7. [Performance Issues](#performance-issues)
8. [Installation & Dependencies](#installation--dependencies)
9. [Data Integrity](#data-integrity)
10. [Emergency Recovery](#emergency-recovery)

---

## Backend Issues

### Issue: Backend Won't Start

**Symptoms:**
```bash
$ uvicorn app:app --reload
ERROR: Error loading ASGI app. Import string "app:app" doesn't exist.
```

**Diagnosis:**
```bash
# Check if you're in the correct directory
pwd  # Should be: /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/backend

# Check if app.py exists
ls -la app.py

# Check Python version
python --version  # Should be 3.12+

# Check virtual environment
which python  # Should point to .venv/bin/python
```

**Solutions:**

1. **Wrong directory:**
   ```bash
   cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/backend
   source ../.venv/bin/activate
   uvicorn app:app --reload --host 0.0.0.0 --port 8601
   ```

2. **Virtual environment not activated:**
   ```bash
   source /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/.venv/bin/activate
   uvicorn app:app --reload --host 0.0.0.0 --port 8601
   ```

3. **Missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Issue: Enhanced Search Not Available

**Symptoms:**
```
WARNING: Enhanced search not available: No module named 'lexa_app.retrieval'
```

**Diagnosis:**
```bash
# Check if module exists
ls -la lexa_app/retrieval.py

# Check PYTHONPATH
echo $PYTHONPATH

# Try importing manually
python -c "from lexa_app.retrieval import enhanced_search"
```

**Solutions:**

1. **Missing PYTHONPATH:**
   ```bash
   export PYTHONPATH=/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/backend:$PYTHONPATH
   uvicorn app:app --reload --host 0.0.0.0 --port 8601
   ```

2. **Import error in retrieval.py:**
   ```bash
   # Check for syntax errors
   python -m py_compile lexa_app/retrieval.py

   # Check dependencies
   pip list | grep -E 'chromadb|openai|rank-bm25'
   ```

3. **ChromaDB not initialized:**
   ```bash
   # Check if ChromaDB directory exists
   ls -la chroma_db/

   # If missing, initialize with indexer
   python -m indexer.pipeline
   ```

### Issue: Hybrid AI System Not Loading

**Symptoms:**
```
WARNING: Hybrid AI not available: No module named 'lexa_app.hybrid_ai'
```

**Diagnosis:**
```bash
# Check if hybrid modules exist
ls -la lexa_app/hybrid_ai.py
ls -la lexa_app/hybrid_endpoints.py
ls -la lexa_app/providers/

# Check OpenAI API key
echo $OPENAI_API_KEY
```

**Solutions:**

1. **Missing OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   # Or add to backend/.env:
   echo 'OPENAI_API_KEY=sk-...' >> backend/.env
   ```

2. **Module import errors:**
   ```bash
   # Test hybrid AI import
   cd backend
   python -c "from lexa_app.hybrid_ai import hybrid_ai_service"
   ```

3. **Provider initialization failure:**
   ```bash
   # Check OpenAI connectivity
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"

   # Check Ollama (if using local AI)
   curl http://localhost:11434/api/tags
   ```

### Issue: Port Already in Use

**Symptoms:**
```
ERROR: [Errno 98] Address already in use
```

**Diagnosis:**
```bash
# Find process using port 8601
sudo lsof -i :8601
sudo netstat -tlnp | grep 8601
```

**Solutions:**

1. **Kill existing process:**
   ```bash
   # Find PID
   sudo lsof -i :8601
   # Output: python 12345 bizbots24 ...

   # Kill the process
   kill 12345

   # Or kill all uvicorn processes
   pkill -f uvicorn
   ```

2. **Use different port:**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8602
   ```

3. **Check for zombie processes:**
   ```bash
   ps aux | grep uvicorn
   pkill -9 -f uvicorn
   ```

---

## Frontend Issues

### Issue: Frontend Won't Start

**Symptoms:**
```bash
$ npm run dev
sh: 1: vite: not found
```

**Diagnosis:**
```bash
# Check if you're in frontend directory
pwd  # Should be: .../Lexa_AI_V2/frontend

# Check if node_modules exists
ls -la node_modules/

# Check npm version
npm --version
node --version
```

**Solutions:**

1. **Dependencies not installed:**
   ```bash
   cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/frontend
   npm install
   npm run dev
   ```

2. **Wrong Node.js version:**
   ```bash
   # Install nvm if needed
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

   # Install Node 18+
   nvm install 18
   nvm use 18
   npm install
   npm run dev
   ```

3. **Port conflict (8082):**
   ```bash
   # Check what's using port 8082
   sudo lsof -i :8082

   # Change port in vite.config.ts
   # server: { port: 8083 }
   ```

### Issue: CORS Errors

**Symptoms:**
```
Access to fetch at 'http://localhost:8601/api/chat' from origin 'http://localhost:8082'
has been blocked by CORS policy
```

**Diagnosis:**
```bash
# Check frontend origin
echo "Frontend running at: http://localhost:8082"

# Check backend CORS config in app.py
grep -A 10 "ALLOWED_ORIGINS" backend/app.py
```

**Solutions:**

1. **Add frontend origin to backend:**

   Edit `backend/app.py`, find `ALLOWED_ORIGINS` list and ensure it includes:
   ```python
   ALLOWED_ORIGINS = [
       "http://localhost:8082",  # ← Ensure this is present
       "http://localhost:5173",
       # ... other origins
   ]
   ```

2. **Restart backend:**
   ```bash
   # If running in tmux, restart uvicorn
   # If running as service:
   sudo systemctl restart lexa-backend.service
   ```

3. **Check browser console:**
   ```
   Press F12 → Network tab → Look for OPTIONS request
   Should return 200 OK with Access-Control-Allow-Origin header
   ```

### Issue: API Calls Failing

**Symptoms:**
```
Failed to fetch
Network request failed
```

**Diagnosis:**
```bash
# Test backend health endpoint
curl http://localhost:8601/api/health

# Check if backend is running
sudo systemctl status lexa-backend.service
# Or for tmux: ps aux | grep uvicorn

# Check frontend API base URL
grep -r "localhost:8601" frontend/src/
```

**Solutions:**

1. **Backend not running:**
   ```bash
   cd backend
   source ../.venv/bin/activate
   uvicorn app:app --reload --host 0.0.0.0 --port 8601
   ```

2. **Wrong API URL in frontend:**

   Check `frontend/src/lib/api.ts`:
   ```typescript
   const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8601';
   ```

3. **Network firewall blocking:**
   ```bash
   # Allow port 8601 (backend)
   sudo ufw allow 8601/tcp

   # Allow port 8082 (frontend dev)
   sudo ufw allow 8082/tcp
   ```

---

## Indexing & Document Processing

### Issue: Documents Not Being Indexed

**Symptoms:**
- New files added to `Database/` but not appearing in search results
- Watcher logs show no activity

**Diagnosis:**
```bash
# Check if watcher is running
ps aux | grep watch.py

# Check Database directory
ls -la backend/Database/

# Check watcher logs
sudo journalctl -u ai-bridge-watcher.service -n 50
# Or if running manually: check tmux window output

# Test manual indexing
cd backend
python -m indexer.pipeline
```

**Solutions:**

1. **Watcher not running:**
   ```bash
   # Start watcher manually
   cd backend
   source ../.venv/bin/activate
   python -m indexer.watch

   # Or start as service
   sudo systemctl start ai-bridge-watcher.service
   ```

2. **File permissions:**
   ```bash
   # Check if watcher user can read files
   ls -la backend/Database/

   # Fix permissions
   chmod -R 755 backend/Database/
   ```

3. **File format not supported:**
   ```bash
   # Check file extension
   # Supported: .pdf, .docx, .txt, .md, .pptx, .xlsx, .csv, .rtf

   # Convert unsupported format or rename
   mv document.doc document.docx
   ```

4. **Cache preventing reindex:**
   ```bash
   # Clear cache and force reindex
   rm -rf backend/Database/.lexa-cache/*
   cd backend
   python -m indexer.pipeline
   ```

### Issue: OCR Not Working

**Symptoms:**
```
WARNING: OCR failed for document.pdf
```

**Diagnosis:**
```bash
# Check if tesseract is installed
which tesseract
tesseract --version

# Check if poppler is installed
which pdftoppm
pdftoppm -v

# Check environment variable
echo $LEXA_DISABLE_OCR
```

**Solutions:**

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr poppler-utils
   ```

2. **Install Python dependencies:**
   ```bash
   pip install pytesseract pdf2image pillow
   ```

3. **Test OCR manually:**
   ```bash
   cd backend
   python -c "
   from indexer.ocr import extract_text_with_ocr
   text = extract_text_with_ocr('Database/document.pdf')
   print(text[:100])
   "
   ```

4. **Check OCR threshold:**
   ```bash
   # If document has few words, OCR won't trigger
   # Default threshold: 50 words

   # Lower threshold temporarily
   export LEXA_OCR_WORD_THRESHOLD=10
   python -m indexer.pipeline
   ```

### Issue: Table Extraction Fails

**Symptoms:**
```
WARNING: Table extraction failed for document.pdf
```

**Diagnosis:**
```bash
# Check if Camelot is installed
pip list | grep camelot

# Check Ghostscript (required for Camelot)
which gs
gs --version

# Check environment variable
echo $LEXA_DISABLE_TABLES
```

**Solutions:**

1. **Install Camelot and dependencies:**
   ```bash
   sudo apt-get install -y ghostscript
   pip install camelot-py[cv]
   ```

2. **Test table extraction:**
   ```bash
   cd backend
   python -c "
   from indexer.tables import extract_tables
   tables = extract_tables('Database/document.pdf')
   print(f'Found {len(tables)} tables')
   "
   ```

3. **Skip table extraction if not needed:**
   ```bash
   export LEXA_DISABLE_TABLES=1
   python -m indexer.pipeline
   ```

### Issue: Chunking Errors

**Symptoms:**
```
ERROR: Failed to chunk document: list index out of range
```

**Diagnosis:**
```bash
# Check document content
cd backend
python -c "
import pymupdf
doc = pymupdf.open('Database/document.pdf')
print(f'Pages: {len(doc)}')
for page in doc:
    text = page.get_text()
    print(f'Page text length: {len(text)}')
"
```

**Solutions:**

1. **Document is empty or corrupted:**
   ```bash
   # Try opening in another PDF viewer
   # If corrupted, re-download or re-scan
   ```

2. **Adjust chunk size:**
   ```bash
   # Increase chunk token size
   export LEXA_CHUNK_TOKENS=1200
   python -m indexer.pipeline
   ```

3. **Skip problematic document:**
   ```bash
   # Move to temporary location
   mv backend/Database/problematic.pdf /tmp/

   # Index other documents
   python -m indexer.pipeline

   # Debug the problematic one separately
   ```

---

## ChromaDB & Vector Search

### Issue: ChromaDB Connection Failed

**Symptoms:**
```
ERROR: Failed to connect to ChromaDB: [Errno 2] No such file or directory
```

**Diagnosis:**
```bash
# Check if ChromaDB directory exists
ls -la backend/chroma_db/

# Check permissions
ls -ld backend/chroma_db/

# Check disk space
df -h
```

**Solutions:**

1. **Create ChromaDB directory:**
   ```bash
   mkdir -p backend/chroma_db
   chmod 755 backend/chroma_db
   ```

2. **Initialize ChromaDB:**
   ```bash
   cd backend
   python -c "
   import chromadb
   client = chromadb.PersistentClient(path='./chroma_db')
   collection = client.get_or_create_collection(name='lexa_documents')
   print(f'Collection has {collection.count()} documents')
   "
   ```

3. **Disk space full:**
   ```bash
   # Check disk usage
   df -h

   # Clean up old logs/cache
   sudo journalctl --vacuum-size=100M
   rm -rf backend/Database/.lexa-cache/*
   ```

### Issue: Embeddings Failing

**Symptoms:**
```
ERROR: OpenAI API error: Incorrect API key provided
```

**Diagnosis:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Solutions:**

1. **Set API key:**
   ```bash
   export OPENAI_API_KEY="sk-proj-..."

   # Or add to .env
   echo 'OPENAI_API_KEY=sk-proj-...' >> backend/.env
   ```

2. **Invalid API key:**
   ```bash
   # Get new key from: https://platform.openai.com/api-keys
   # Update .env file
   ```

3. **Rate limit exceeded:**
   ```bash
   # Wait a few minutes
   sleep 60

   # Or upgrade OpenAI plan
   # https://platform.openai.com/account/billing
   ```

4. **Network connectivity:**
   ```bash
   # Test internet connection
   ping -c 3 api.openai.com

   # Check proxy settings
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

### Issue: No Search Results

**Symptoms:**
- Query returns empty results
- "I don't have enough information" responses

**Diagnosis:**
```bash
# Check collection size
cd backend
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('lexa_documents')
print(f'Total documents: {collection.count()}')
"

# Check if query works manually
python -c "
from lexa_app.retrieval import enhanced_search
result = enhanced_search('test query')
print(result)
"
```

**Solutions:**

1. **No documents indexed:**
   ```bash
   # Index documents
   cd backend
   python -m indexer.pipeline
   ```

2. **Query too specific:**
   ```bash
   # Try broader query
   # Instead of: "What is the PTO policy for part-time employees hired after 2023?"
   # Try: "PTO policy"
   ```

3. **Collection name mismatch:**

   Check `backend/lexa_app/retrieval.py` and `backend/indexer/store.py` use same collection name:
   ```python
   COLLECTION_NAME = "lexa_documents"  # Should match in both files
   ```

4. **Corrupted ChromaDB:**
   ```bash
   # Backup current DB
   cp -r backend/chroma_db backend/chroma_db.backup

   # Delete and reindex
   rm -rf backend/chroma_db
   mkdir backend/chroma_db
   python -m indexer.pipeline
   ```

---

## Authentication & Sessions

### Issue: Admin Login Fails

**Symptoms:**
- "Invalid password" error
- Can't access admin panel

**Diagnosis:**
```bash
# Check admin password environment variable
echo $ADMIN_PASSWORD

# Check if it's set in .env
grep ADMIN_PASSWORD backend/.env

# Check app.py default
grep "ADMIN_PASSWORD" backend/app.py
```

**Solutions:**

1. **Use default password:**
   ```
   Default password: Krypt0n!t3
   ```

2. **Set custom password:**
   ```bash
   export ADMIN_PASSWORD="your-secure-password"

   # Or in backend/.env:
   echo 'ADMIN_PASSWORD=your-secure-password' >> backend/.env

   # Restart backend
   sudo systemctl restart lexa-backend.service
   ```

3. **Password contains special characters:**
   ```bash
   # Ensure password is properly quoted in .env
   # backend/.env:
   ADMIN_PASSWORD="P@ssw0rd!"  # ← Use quotes
   ```

### Issue: Session Expires Immediately

**Symptoms:**
- Logged out after refresh
- "Session expired" errors

**Diagnosis:**
```bash
# Check SECRET_KEY
echo $SECRET_KEY

# Check browser cookies
# F12 → Application → Cookies → Look for "lexa_session"

# Check session max age in app.py
grep -A 5 "max_age" backend/app.py
```

**Solutions:**

1. **SECRET_KEY not set:**
   ```bash
   # Generate secure key
   python -c "import secrets; print(secrets.token_hex(32))"

   # Set in .env
   echo 'SECRET_KEY=<generated-key>' >> backend/.env

   # Restart backend
   sudo systemctl restart lexa-backend.service
   ```

2. **SECRET_KEY changed:**
   ```bash
   # All existing sessions are invalidated when SECRET_KEY changes
   # Users need to log in again
   # This is expected behavior
   ```

3. **Cookie domain mismatch:**

   Check `backend/app.py` session cookie settings:
   ```python
   response.set_cookie(
       key="lexa_session",
       value=token,
       max_age=86400,  # 24 hours
       httponly=True,
       secure=True,  # ← May cause issues on HTTP
       samesite="none",  # ← May need "lax" for localhost
       domain=".bizbots24.com"  # ← Remove for localhost
   )
   ```

4. **Development on localhost:**

   For local development, modify session cookie in `app.py`:
   ```python
   response.set_cookie(
       key="lexa_session",
       value=token,
       max_age=86400,
       httponly=True,
       secure=False,  # ← Set to False for HTTP
       samesite="lax",  # ← Set to lax for localhost
       # domain not set for localhost
   )
   ```

---

## API & Network Issues

### Issue: 502 Bad Gateway

**Symptoms:**
```
502 Bad Gateway
nginx/1.18.0
```

**Diagnosis:**
```bash
# Check if backend is running
curl http://localhost:8601/api/health

# Check nginx error logs
sudo tail -n 50 /var/log/nginx/error.log

# Check if nginx can reach backend
sudo netstat -tlnp | grep 8601
```

**Solutions:**

1. **Backend not running:**
   ```bash
   sudo systemctl start lexa-backend.service
   sudo systemctl status lexa-backend.service
   ```

2. **Nginx proxy misconfigured:**

   Check `/etc/nginx/sites-available/lexaai`:
   ```nginx
   location /api/ {
       proxy_pass http://127.0.0.1:8601/api/;  # ← Ensure correct port
       proxy_http_version 1.1;
       proxy_set_header Host $host;
   }
   ```

3. **Restart nginx:**
   ```bash
   sudo nginx -t  # Test config
   sudo systemctl restart nginx
   ```

### Issue: Slow API Response

**Symptoms:**
- Queries take > 10 seconds
- Timeout errors

**Diagnosis:**
```bash
# Test query timing
time curl -X POST "http://localhost:8601/api/chat?query=test"

# Check backend logs for bottlenecks
sudo journalctl -u lexa-backend.service -f

# Check system resources
top
htop
```

**Solutions:**

1. **Too many documents in collection:**
   ```bash
   # Check collection size
   cd backend
   python -c "
   import chromadb
   client = chromadb.PersistentClient(path='./chroma_db')
   collection = client.get_collection('lexa_documents')
   print(f'Total chunks: {collection.count()}')
   "

   # If > 100,000 chunks, consider pruning old documents
   ```

2. **Increase Uvicorn workers:**

   Edit `deployment/lexa-backend.service`:
   ```ini
   ExecStart=/opt/lexa/backend/.venv/bin/uvicorn app:app \
       --workers 4  # ← Increase from 2 to 4
   ```

3. **Optimize BM25 re-ranking:**

   Edit `backend/lexa_app/retrieval.py`:
   ```python
   # Reduce initial results
   results = self.collection.query(
       query_embeddings=[query_embedding],
       n_results=20  # ← Reduce from 30
   )
   ```

4. **Enable caching:**
   ```bash
   # Check if FAQ cache is working
   ls -la backend/data/faq_cache.json
   ```

---

## Performance Issues

### Issue: High Memory Usage

**Symptoms:**
- Backend using > 2GB RAM
- OOM (Out of Memory) errors

**Diagnosis:**
```bash
# Check memory usage
free -h

# Check backend process
ps aux | grep uvicorn

# Check systemd resource limits
sudo systemctl show lexa-backend.service | grep Memory
```

**Solutions:**

1. **Reduce Uvicorn workers:**

   Edit `deployment/lexa-backend.service`:
   ```ini
   ExecStart=/opt/lexa/backend/.venv/bin/uvicorn app:app \
       --workers 1  # ← Reduce workers
   ```

2. **Clear ChromaDB cache:**
   ```bash
   cd backend
   python -c "
   import chromadb
   client = chromadb.PersistentClient(path='./chroma_db')
   # ChromaDB automatically manages memory
   # But you can restart to clear cache
   "

   sudo systemctl restart lexa-backend.service
   ```

3. **Limit collection size:**
   ```bash
   # Remove old/unused documents
   cd backend
   python -c "
   import chromadb
   client = chromadb.PersistentClient(path='./chroma_db')
   collection = client.get_collection('lexa_documents')
   # Delete documents by IDs or metadata filter
   "
   ```

### Issue: High CPU Usage

**Symptoms:**
- CPU at 100% constantly
- System unresponsive

**Diagnosis:**
```bash
# Check CPU usage by process
top
htop

# Check if OCR is running
ps aux | grep tesseract

# Check if embeddings are being generated
ps aux | grep python
```

**Solutions:**

1. **OCR running on large documents:**
   ```bash
   # Disable OCR temporarily
   export LEXA_DISABLE_OCR=1

   # Or increase word threshold
   export LEXA_OCR_WORD_THRESHOLD=100
   ```

2. **Reduce CPU quota:**

   Edit `deployment/lexa-backend.service`:
   ```ini
   [Service]
   CPUQuota=100%  # ← Reduce from 200%
   ```

3. **Batch document processing:**
   ```bash
   # Instead of watching directory, index in batches
   # Stop watcher
   sudo systemctl stop ai-bridge-watcher.service

   # Index manually during off-hours
   cd backend
   python -m indexer.pipeline
   ```

---

## Installation & Dependencies

### Issue: pip install Fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement camelot-py[cv]
```

**Diagnosis:**
```bash
# Check Python version
python --version  # Should be 3.12+

# Check pip version
pip --version

# Check if inside virtual environment
which python
```

**Solutions:**

1. **Upgrade pip:**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Install system dependencies first:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y \
       python3.12-dev \
       build-essential \
       libopencv-dev \
       ghostscript \
       tesseract-ocr \
       poppler-utils
   ```

3. **Install requirements in order:**
   ```bash
   # Core dependencies first
   pip install fastapi uvicorn chromadb openai

   # Then document processing
   pip install pymupdf python-docx

   # Then optional (OCR, tables)
   pip install pytesseract pdf2image camelot-py[cv]

   # Finally remaining
   pip install -r requirements.txt
   ```

### Issue: bcrypt Version Conflict

**Symptoms:**
```
ERROR: bcrypt 4.1.0 conflicts with passlib requirements
```

**Diagnosis:**
```bash
pip list | grep bcrypt
pip list | grep passlib
```

**Solutions:**

1. **Install correct bcrypt version:**
   ```bash
   pip install "bcrypt<4.1"
   ```

2. **Reinstall passlib:**
   ```bash
   pip uninstall passlib bcrypt
   pip install passlib "bcrypt<4.1"
   ```

---

## Data Integrity

### Issue: Duplicate Sources in Results

**Symptoms:**
- Same document appears multiple times in sources
- Sources list shows "document.pdf (page 5)" three times

**Diagnosis:**
```bash
# Check if document was indexed multiple times
cd backend
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('lexa_documents')
results = collection.get(where={'file': 'document.pdf'})
print(f'Chunks from document.pdf: {len(results[\"ids\"])}')
"
```

**Solutions:**

1. **Reindex with fresh ChromaDB:**
   ```bash
   # Backup current DB
   cp -r backend/chroma_db backend/chroma_db.backup

   # Clear collection
   rm -rf backend/chroma_db
   mkdir backend/chroma_db

   # Clear cache
   rm -rf backend/Database/.lexa-cache/*

   # Reindex
   python -m indexer.pipeline
   ```

2. **Deduplication in retrieval:**

   The `enhanced_search` function in `backend/lexa_app/retrieval.py` already deduplicates sources. If you still see duplicates, check the deduplication logic.

### Issue: Incorrect Page Numbers

**Symptoms:**
- Source citations show wrong page numbers
- "Found on page 10" but actually on page 1

**Diagnosis:**
```bash
# Check metadata in ChromaDB
cd backend
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('lexa_documents')
results = collection.get(limit=5)
import json
for metadata in results['metadatas']:
    print(json.dumps(metadata, indent=2))
"
```

**Solutions:**

1. **Reindex with correct page extraction:**
   ```bash
   # Clear cache and reindex
   rm -rf backend/Database/.lexa-cache/*
   cd backend
   python -m indexer.pipeline
   ```

2. **Verify page extraction logic:**
   ```bash
   # Test page extraction
   cd backend
   python -c "
   import pymupdf
   doc = pymupdf.open('Database/document.pdf')
   for page_num, page in enumerate(doc):
       text = page.get_text()[:100]
       print(f'Page {page_num}: {text}')
   "
   ```

---

## Emergency Recovery

### Issue: Complete System Failure

**Symptoms:**
- Nothing works
- Backend won't start
- Frontend errors everywhere

**Recovery Steps:**

1. **Stop all services:**
   ```bash
   sudo systemctl stop lexa-backend.service
   sudo systemctl stop ai-bridge-watcher.service
   pkill -f uvicorn
   pkill -f vite
   ```

2. **Backup current state:**
   ```bash
   cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2

   # Backup ChromaDB
   cp -r backend/chroma_db backend/chroma_db.emergency_backup

   # Backup settings
   cp -r backend/storage backend/storage.emergency_backup

   # Note current git state
   git status > emergency_git_status.txt
   git log -1 >> emergency_git_status.txt
   ```

3. **Rollback to last working commit:**
   ```bash
   # Find last working commit
   git log --oneline -10

   # Checkout stable version
   git checkout main  # or specific commit hash
   ```

4. **Reinstall dependencies:**
   ```bash
   source .venv/bin/activate
   pip install --force-reinstall -r backend/requirements.txt

   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **Restart services:**
   ```bash
   # Development mode
   cd backend
   source ../.venv/bin/activate
   uvicorn app:app --reload --host 0.0.0.0 --port 8601

   # In another terminal
   cd frontend
   npm run dev
   ```

6. **Verify health:**
   ```bash
   curl http://localhost:8601/api/health
   curl http://localhost:8082
   ```

### Issue: ChromaDB Corrupted

**Symptoms:**
```
ERROR: Database disk image is malformed
sqlite3.DatabaseError
```

**Recovery Steps:**

1. **Stop backend:**
   ```bash
   sudo systemctl stop lexa-backend.service
   ```

2. **Attempt SQLite repair:**
   ```bash
   cd backend/chroma_db

   # Find SQLite database
   find . -name "*.sqlite3"

   # Dump and restore
   sqlite3 chroma.sqlite3 ".dump" | sqlite3 chroma_repaired.sqlite3

   # Replace original
   mv chroma.sqlite3 chroma.sqlite3.corrupted
   mv chroma_repaired.sqlite3 chroma.sqlite3
   ```

3. **If repair fails, restore from backup:**
   ```bash
   # Use most recent backup
   rm -rf backend/chroma_db
   cp -r backend/chroma_db.backup backend/chroma_db
   ```

4. **If no backup, rebuild from scratch:**
   ```bash
   rm -rf backend/chroma_db
   mkdir backend/chroma_db

   # Clear cache
   rm -rf backend/Database/.lexa-cache/*

   # Reindex all documents
   cd backend
   python -m indexer.pipeline
   ```

5. **Restart backend:**
   ```bash
   sudo systemctl start lexa-backend.service
   sudo systemctl status lexa-backend.service
   ```

---

## Getting Help

### Diagnostic Information to Collect

When reporting issues, collect this information:

```bash
# System info
uname -a
python --version
node --version
npm --version

# Service status
sudo systemctl status lexa-backend.service
ps aux | grep uvicorn

# Logs
sudo journalctl -u lexa-backend.service -n 100

# Dependencies
pip list
pip show chromadb openai

# ChromaDB status
cd backend
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('lexa_documents')
print(f'Collection count: {collection.count()}')
"

# Disk space
df -h

# Environment variables (NEVER share API keys!)
env | grep LEXA_
env | grep ADMIN_PASSWORD  # ← Redact this before sharing!
```

### Support Resources

- **Documentation:** Check `docs/` directory
- **Architecture:** `docs/ARCHITECTURE.md`
- **Operations:** `docs/RUNBOOK.md`
- **Indexing:** `docs/INDEXING.md`
- **Services:** `docs/SERVICES.md`

### Common Fixes Checklist

Before reporting issues, try these:

- [ ] Restart backend: `sudo systemctl restart lexa-backend.service`
- [ ] Clear cache: `rm -rf backend/Database/.lexa-cache/*`
- [ ] Check logs: `sudo journalctl -u lexa-backend.service -n 50`
- [ ] Verify API key: `echo $OPENAI_API_KEY`
- [ ] Test health endpoint: `curl http://localhost:8601/api/health`
- [ ] Check disk space: `df -h`
- [ ] Verify permissions: `ls -la backend/`
- [ ] Test ChromaDB: `python -c "import chromadb; print('OK')"`
- [ ] Reinstall deps: `pip install -r backend/requirements.txt`
- [ ] Restart system: `sudo reboot`

---

## See Also

- [RUNBOOK.md](RUNBOOK.md) - Operational procedures
- [SERVICES.md](SERVICES.md) - Service management
- [INDEXING.md](INDEXING.md) - Document processing pipeline
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
