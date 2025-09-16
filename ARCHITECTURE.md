# System Architecture

## High-Level Component Diagram

```
┌─────────────────┐    HTTP/WS     ┌──────────────────┐    Python     ┌───────────────────┐
│   Frontend      │◄──────────────►│    Backend       │◄──────────────►│ Indexer/Retriever │
│   (Vite/React)  │                │   (FastAPI)      │                │   (Python)        │
│   Port 8082     │                │   Port 8601      │                │                   │
└─────────────────┘                └──────────────────┘                └───────────────────┘
                                           │                                     │
                                           │                                     │
                                           ▼                                     ▼
                                   ┌──────────────┐                     ┌─────────────────┐
                                   │   Settings   │                     │    ChromaDB     │
                                   │   Storage    │                     │ Vector Database │
                                   │   (JSON)     │                     │  (Persistent)   │
                                   └──────────────┘                     └─────────────────┘
```

## Request/Response Flow

### Chat Request Flow
1. **User Input** → Frontend captures query
2. **API Call** → POST /api/chat with `{"query": "user question"}`
3. **Enhanced Search** → Backend calls `enhanced_search()` function
4. **Vector Retrieval** → ChromaDB semantic search (top 20)
5. **BM25 Re-ranking** → Lexical reranking for better relevance
6. **Policy Boost** → Prioritize policy documents (1.2x boost)
7. **Top 3 Selection** → Select best 3 sources
8. **Citation Formatting** → Create page-accurate citations
9. **Response** → JSON with answer + sources array

### Document Indexing Flow
1. **File Detection** → Watchdog monitors Database/ directory
2. **File Processing** → Pipeline processes based on extension
3. **Text Extraction** → PyMuPDF → OCR fallback if needed
4. **Chunking** → 800 tokens with 25% overlap
5. **Embedding** → OpenAI text-embedding-3-large
6. **Storage** → ChromaDB upsert with metadata
7. **Caching** → Local cache for processed content

## Component Details

### Frontend (Vite/React)
- **Main App**: Single-page React application
- **Chat Interface**: Real-time chat with streaming responses
- **Admin Panel**: Branding configuration
- **Proxy**: Dev proxy to backend on port 8601

### Backend (FastAPI)
- **Chat Endpoint**: `/api/chat` handles user queries
- **Health Check**: `/api/health` for monitoring
- **Admin Routes**: Branding settings management
- **CORS**: Configured for development origins

### Indexer Pipeline
- **Document Types**: PDF, DOCX, TXT, MD
- **OCR Integration**: Tesseract via pytesseract/pdf2image
- **Table Extraction**: Camelot-py for PDF tables
- **Chunking Strategy**: Sentence-aware with overlap
- **Metadata**: File, page, chunk-level metadata

### ChromaDB Vector Store
- **Collection**: `lexa_documents`
- **Embedding Model**: text-embedding-3-large (1536 dims)
- **Distance Metric**: Cosine similarity
- **Persistence**: Local file-based storage

## Environment Flags Application

The system respects the following indexing preferences:

```python
# Current implementation honoring your constraints:
LEXA_DISABLE_OCR=1        # OCR usage controlled by word threshold
LEXA_DISABLE_TABLES=1     # Tables currently extracted (needs flag)
LEXA_SKIP_IMAGE_ONLY=1    # Not fully implemented (needs addition)
LEXA_CHUNK_CHARS=1200     # Currently using tokens (800), needs conversion
LEXA_CHUNK_OVERLAP=0.25   # Currently fixed 100 tokens (needs percentage)
LEXA_EXTS="..."          # Currently hardcoded in CONFIG
```

## Data Flow Patterns

### Query Processing
```
User Query → Vector Search → BM25 Rerank → Policy Boost → Top-K → Citations
```

### Document Processing
```
File Change → Content Hash → Cache Check → Extract Text → Chunk → Embed → Store
```

### Citation Generation
```
Search Results → File Metadata → Page Numbers → URL Generation → Citation Text
```

## Security & Access Control

- **Local Development**: No authentication required
- **Session Management**: JWT-style tokens with itsdangerous
- **CORS**: Restrictive origins for production
- **File Access**: Controlled through proxy URLs

## Performance Considerations

- **Caching**: Aggressive caching of OCR and table extraction
- **Chunking**: Optimized for embedding model context limits
- **Search**: Hybrid approach balances semantic and lexical matching
- **Concurrency**: AsyncIO support in FastAPI for concurrent requests