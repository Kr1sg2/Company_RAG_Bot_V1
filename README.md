# Lexa AI V2 Chatbot

A production-ready AI chatbot system with FastAPI backend, Vite frontend, and ChromaDB vector search for enterprise document retrieval.

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- tmux (for development session management)
- System packages: `poppler-utils tesseract-ocr ghostscript` (for PDF processing)

### Development Setup

1. **Start the development environment:**
   ```bash
   cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2
   ./start_lexa.sh
   ```

2. **Access the application:**
   - Frontend: http://localhost:8082
   - Backend API: http://localhost:8601/api/docs
   - Admin Interface: http://localhost:8082/admin/branding

### Backend Setup (Manual)
```bash
cd Backend_FastAPI
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8601 --reload
```

### Frontend Setup (Manual)
```bash
cd frontend
npm install
npm run dev
```

## Testing the System

### Test Backend API
```bash
# Health check
curl http://localhost:8601/api/health

# Test chat endpoint
curl -X POST http://localhost:8601/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the PTO policy for 6 years of employment?"}'
```

### Rebuild Index
```bash
cd Backend_FastAPI
python -m indexer.reindex Database/
```

## Key Features

- **OCR-Aware Document Processing**: Automatically detects when OCR is needed for better text extraction
- **Hybrid Search**: Combines semantic (vector) and lexical (BM25) search with policy document prioritization
- **Multi-format Support**: PDF, DOCX, TXT, MD files with appropriate parsing
- **Chunk-aware Retrieval**: 800-1200 token chunks with 25% overlap for optimal context
- **Real-time Updates**: File watching for automatic re-indexing
- **Clean Citations**: Page-accurate source references with direct file links

## Architecture

```
Frontend (Vite/React) ←→ Backend (FastAPI) ←→ Indexer/Retriever ←→ ChromaDB
         Port 8082           Port 8601         Python Modules      Vector Store
```

## Environment Configuration

Key environment variables (optional, with defaults):
- `LEXA_CHUNK_TOKENS=800` - Token count per chunk
- `LEXA_EMBED_MODEL=text-embedding-3-large` - OpenAI embedding model
- `LEXA_WATCH_DIR=Database` - Directory to monitor for documents
- `LEXA_OCR_WORD_THRESHOLD=50` - Min words before OCR activation

## Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed production setup instructions.

## Documentation

- [API.md](./API.md) - API endpoint reference
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and data flow
- [INDEXING.md](./INDEXING.md) - Document processing pipeline
- [CONFIG.md](./CONFIG.md) - Configuration options
- [FRONTEND.md](./FRONTEND.md) - Frontend architecture
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment guide