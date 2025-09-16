# Configuration Reference

## Environment Variables

### Indexing Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LEXA_WATCH_DIR` | string | `"Database"` | Directory to monitor for documents |
| `LEXA_CACHE_DIR` | string | `"Database/.lexa-cache"` | Cache directory for processed content |
| `LEXA_CHUNK_TOKENS` | integer | `800` | Target tokens per chunk (current implementation) |
| `LEXA_CHUNK_CHARS` | integer | `1200` | Target characters per chunk (recommended) |
| `LEXA_CHUNK_OVERLAP` | float | `0.25` | Overlap percentage between chunks |
| `LEXA_OCR_WORD_THRESHOLD` | integer | `50` | Minimum words before OCR is triggered |
| `LEXA_EMBED_MODEL` | string | `"text-embedding-3-large"` | OpenAI embedding model |

### Feature Toggles

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LEXA_DISABLE_OCR` | boolean | `0` | Disable OCR processing entirely |
| `LEXA_DISABLE_TABLES` | boolean | `0` | Skip table extraction from PDFs |
| `LEXA_SKIP_IMAGE_ONLY` | boolean | `0` | Skip pages that contain only images |

### File Processing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LEXA_EXTS` | string | `".pdf,.docx,.doc,.pptx,.ppt,.txt,.md,.rtf,.xlsx,.xls,.csv"` | Comma-separated list of allowed file extensions |

### Database Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LEXA_CHROMA_PATH` | string | `"chroma_db"` | Path to ChromaDB persistence directory |
| `CHROMA_PERSIST_DIR` | string | `"chroma_db"` | Alternative name for ChromaDB directory |
| `CHROMA_DB_DIR` | string | `"chroma_db"` | Alternative name for ChromaDB directory |

### Backend Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ADMIN_PASSWORD` | string | `"Krypt0n!t3"` | Admin panel password |
| `SECRET_KEY` | string | `"your-secret-key-change-me"` | Session signing key |
| `PUBLIC_HOST` | string | `""` | Public host URL for file links |

### OpenAI Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | string | *required* | OpenAI API key for embeddings |

## Configuration Files

### Backend Settings Storage
Location: `Backend_FastAPI/storage/settings.json`

```json
{
  "branding": {
    "companyName": "Leader's Casual Furniture",
    "primaryColor": "#2563eb",
    "secondaryColor": "#64748b",
    "logoUrl": ""
  }
}
```

### Indexer Configuration
Location: `Backend_FastAPI/indexer/__init__.py`

```python
CONFIG = {
    "WATCH_DIR": os.getenv("LEXA_WATCH_DIR", "Database"),
    "CACHE_DIR": os.getenv("LEXA_CACHE_DIR", "Database/.lexa-cache"),
    "ALLOWED_EXT": {".pdf", ".docx", ".txt", ".md"},
    "IGNORE_DIRS": {".lexa-cache", "__pycache__"},
    "CHUNK_TOKENS": int(os.getenv("LEXA_CHUNK_TOKENS", "800")),
    "OCR_WORD_THRESHOLD": int(os.getenv("LEXA_OCR_WORD_THRESHOLD", "50")),
    "EMBED_MODEL": os.getenv("LEXA_EMBED_MODEL", "text-embedding-3-large"),
}
```

### Frontend Configuration
Location: `frontend/.env.local`

```env
VITE_API_BASE_URL=http://localhost:8601
```

## Configuration Examples

### Minimal OCR Setup
```bash
export LEXA_DISABLE_OCR=1
export LEXA_DISABLE_TABLES=1
export LEXA_SKIP_IMAGE_ONLY=1
```

### Character-Based Chunking
```bash
export LEXA_CHUNK_CHARS=1200
export LEXA_CHUNK_OVERLAP=0.25
```

### Custom File Types
```bash
export LEXA_EXTS=".pdf,.docx,.txt"
```

### Production Database
```bash
export LEXA_CHROMA_PATH="/var/lib/lexa/chroma_db"
export LEXA_WATCH_DIR="/var/lib/lexa/documents"
export LEXA_CACHE_DIR="/var/lib/lexa/cache"
```

## Development vs Production

### Development Configuration
- OCR enabled for better text extraction
- Aggressive caching for faster development
- No authentication required
- CORS allows localhost origins

### Production Configuration
- Environment-based settings
- Secure session management
- Restricted CORS origins
- Proper logging configuration
- Health check endpoints

## Configuration Validation

### Required Configuration
The system will fail to start without:
- `OPENAI_API_KEY` environment variable
- Write access to cache directory
- Read access to watch directory

### Optional Configuration
Missing optional configuration falls back to sensible defaults:
- Default embedding model
- Default chunk sizes
- Default file extensions
- Local database storage

## Performance Tuning

### Large Document Collections
```bash
# Increase chunk size for fewer total chunks
export LEXA_CHUNK_CHARS=1500

# Reduce overlap for less storage
export LEXA_CHUNK_OVERLAP=0.15

# Disable expensive operations
export LEXA_DISABLE_TABLES=1
```

### Memory Optimization
```bash
# Smaller chunks for lower memory usage
export LEXA_CHUNK_CHARS=800

# Disable OCR to reduce memory peaks
export LEXA_DISABLE_OCR=1
```

### Processing Speed
```bash
# Skip image-heavy documents
export LEXA_SKIP_IMAGE_ONLY=1

# Lower OCR threshold to use OCR less often
export LEXA_OCR_WORD_THRESHOLD=25
```