# Lexa Document Indexer Service

Separate document indexing service with OCR-first pipeline for image-heavy PDFs.

## Installation

### 1) System dependencies
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr ghostscript
```

### 2) Python deps
```bash
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/Backend_FastAPI
source venv/bin/activate
pip install -r requirements.txt
```

### 3) Systemd service
```bash
sudo cp lexa-indexer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lexa-indexer
```

## Usage

### Service Management
```bash
sudo systemctl start lexa-indexer
sudo systemctl status lexa-indexer --no-pager -l
sudo systemctl stop lexa-indexer
sudo journalctl -u lexa-indexer -f
```

### Manual Reindexing
```bash
# Full reindex of watch dir
python -m indexer.reindex

# Reindex one file
python -m indexer.reindex /path/to/document.pdf

# List indexed documents
python -m indexer.reindex --list

# Delete from index by relative path
python -m indexer.reindex --delete "relative/path/to/file.pdf"
```

## Features

- **OCR-first for sparse/image-only pages**
- **Table extraction from PDFs**
- **Caching of OCR/table results**
- **Debounced processing of file changes**
- **Hybrid retrieval: vector + BM25 re-rank**
- **Policy document prioritization**
- **Numeric guardrails for consistent answers**

## Workflow

1. **Add/Modify** in Database/ → auto-index after file stabilizes
2. **Delete** from Database/ → auto-removed from index
3. **Cache** in Database/.lexa-cache/ (ignored by watcher)

## Verify
```bash
python -m indexer.reindex --list
ls -la Database/.lexa-cache/
python - <<'PY'
import chromadb
client = chromadb.PersistentClient('chroma_db')
c = client.get_collection('lexa_documents')
print("Total chunks:", c.count())
PY
```