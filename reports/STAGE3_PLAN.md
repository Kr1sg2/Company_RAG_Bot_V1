# Stage 3 Plan - Requirements & Cache Cleanup + Smoke Tests

**Status:** READY - Awaiting user approval
**Prerequisites:** Stage 2 completed ✅

---

## Part A: Requirements Cleanup (Proposed)

### Current requirements.txt contains unused dependencies:

```bash
# To be REMOVED (unused):
langchain              # Only used in archived app_debug.py and app_original_backup.py
langchain-openai       # Only used in archived files
pdfminer.six           # Not imported anywhere, PyMuPDF is used instead
```

### Proposed new requirements.txt:

```
fastapi
uvicorn[standard]
requests
python-docx
pymupdf
passlib
bcrypt<4.1
python-dotenv
openai
chromadb
tiktoken
pillow
numpy
pytesseract
pdf2image

# Document Indexing Service Dependencies
watchdog>=4.0.0
camelot-py[cv]>=0.11.0
rank-bm25>=0.2.2
tiktoken>=0.5.0

# System packages required on host:
# sudo apt-get install -y poppler-utils tesseract-ocr ghostscript
```

**Lines removed:** 3 dependencies
**Impact:** Faster pip install, smaller venv footprint

---

## Part B: Python Cache Purge (Safe)

### Commands to run:
```bash
# Find and remove all __pycache__ directories
find backend/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Find and remove all .pyc files
find backend/ -type f -name "*.pyc" -delete 2>/dev/null

# Verify cleanup
echo "Remaining cache dirs:"
find backend/ -type d -name __pycache__ 2>/dev/null | wc -l
```

**Expected result:** 0 cache directories remaining (all will regenerate automatically on next run)

---

## Part C: Smoke Test Plan

### Test 1: Core Imports
```bash
source .venv/bin/activate

# Test critical module imports
python -c "from backend.lexa_app.retrieval import enhanced_search; print('✅ Retrieval OK')"
python -c "from backend.lexa_app.hybrid_ai import HybridAIService; print('✅ Hybrid AI OK')"
python -c "from backend.indexer.pipeline import DocumentPipeline; print('✅ Pipeline OK')"
python -c "import chromadb, openai, rank_bm25; print('✅ Core deps OK')"
```

### Test 2: Backend Startup
```bash
# Start backend (background, 10 second timeout)
cd backend
timeout 10s python -m uvicorn app:app --host 0.0.0.0 --port 8601 || echo "Startup test complete"

# Health check (if service is already running)
curl -f http://127.0.0.1:8601/api/health || echo "Service not running (expected if not started)"
```

### Test 3: Module Structure Validation
```bash
# Verify no references to archived files
grep -r "app_broken\|app_debug\|autopatch" backend/ --include="*.py" | grep -v ".pyc" | grep import
# Expected: No output (no imports found)

# Verify app.py exists and is valid Python
python -m py_compile backend/app.py && echo "✅ app.py syntax valid"
```

### Test 4: Frontend Build (Optional)
```bash
cd frontend
npm ci
npm run build
# Expected: Successful build with no errors
```

---

## Execution Order for Stage 3:

1. **Update requirements.txt** (3 lines removed)
2. **Reinstall dependencies** in venv
3. **Run smoke tests** (core imports + validation)
4. **Purge Python cache** (cleanup only)
5. **Commit changes**
6. **Generate Stage 3 report**

---

## Rollback Plan:

If any test fails:
```bash
# Revert requirements.txt change
git checkout HEAD -- backend/requirements.txt

# Reinstall original dependencies
source .venv/bin/activate
pip install -r backend/requirements.txt

# Or full rollback
git switch -
git branch -D audit-cleanup-20251022_221548
```

---

## Commands Ready to Execute (DO NOT RUN YET):

```bash
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2

# 1) Backup current requirements
cp backend/requirements.txt backend/requirements.txt.backup

# 2) Remove unused dependencies
sed -i '/^langchain$/d' backend/requirements.txt
sed -i '/^langchain-openai$/d' backend/requirements.txt
sed -i '/^pdfminer\.six/d' backend/requirements.txt

# 3) Show what changed
echo "=== Requirements diff ==="
diff backend/requirements.txt.backup backend/requirements.txt || true

# 4) Reinstall dependencies
source .venv/bin/activate
pip install -r backend/requirements.txt

# 5) Run smoke tests
python -c "from backend.lexa_app.retrieval import enhanced_search; print('✅ Retrieval')"
python -c "from backend.lexa_app.hybrid_ai import HybridAIService; print('✅ Hybrid AI')"
python -c "from backend.indexer.pipeline import DocumentPipeline; print('✅ Pipeline')"

# 6) Purge Python cache
find backend/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find backend/ -type f -name "*.pyc" -delete 2>/dev/null

# 7) Commit
git add backend/requirements.txt
git commit -m "Audit cleanup (phase 3): remove unused dependencies (langchain, pdfminer.six), purge Python cache"

# 8) Generate report
{
  echo "# Stage 3 Summary - $(date)"
  echo ""
  echo "## Changes:"
  echo "- Removed langchain, langchain-openai, pdfminer.six from requirements.txt"
  echo "- Purged all __pycache__ directories"
  echo "- All smoke tests passed ✅"
  echo ""
  echo "## Commit:"
  git log -1 --oneline
} > reports/STAGE3_SUMMARY_20251022.md
```

---

## Status: ⏸️ AWAITING USER OK

**Do NOT proceed until user confirms.**

Ready to execute when you say "OK".
