# Document Indexing Pipeline

## Overview

The indexing system processes documents in the `Database/` directory with OCR-first approach, intelligent chunking, and comprehensive metadata preservation.

## File Processing Flow

### 1. File Detection
- **Directory Monitoring**: Watchdog monitors `Database/` for changes
- **Supported Extensions**: `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.txt`, `.md`, `.rtf`, `.xlsx`, `.xls`, `.csv`
- **Ignored Directories**: `.lexa-cache`, `__pycache__`

### 2. Content Hash & Caching
```python
# File identification
relative_path, content_hash, doc_id, mtime = get_file_info(file_path, watch_dir)

# Cache check to avoid reprocessing
if cache.has_cached_data(doc_id, content_hash):
    return  # Skip processing
```

### 3. Text Extraction by File Type

#### PDF Processing
1. **Initial Extraction**: PyMuPDF extracts text from each page
2. **Word Count Check**: If page has < 50 words, trigger OCR
3. **OCR Fallback**: Tesseract OCR via pdf2image for scanned pages
4. **Table Extraction**: Camelot-py extracts tables (if enabled)
5. **Content Combination**: Text + table data merged per page

#### DOCX Processing
1. **Paragraph Extraction**: python-docx reads all paragraphs
2. **Text Combination**: Paragraphs joined with newlines
3. **Metadata Addition**: Document-level metadata

#### Text File Processing
1. **Direct Reading**: UTF-8 encoded file reading
2. **Extension Detection**: `.txt`, `.md`, `.rtf` handling
3. **Simple Metadata**: File-level metadata only

## Chunking Strategy

### Current Implementation (Token-Based)
```python
CHUNK_TOKENS = 800  # Target tokens per chunk
OVERLAP_TOKENS = 100  # Fixed overlap between chunks
```

### Chunking Process
1. **Sentence Splitting**: Text split on sentence boundaries (`[.!?]`)
2. **Token Counting**: tiktoken for precise token counts (or 4-char approximation)
3. **Chunk Assembly**: Sentences added until token limit reached
4. **Overlap Addition**: Last ~75 words from previous chunk included
5. **Metadata Preservation**: Page/file metadata carried through each chunk

### Required Chunking Update (Per Your Specs)
```python
# Should be updated to:
CHUNK_CHARS = 1200  # Characters instead of tokens
OVERLAP_PERCENTAGE = 0.25  # 25% overlap instead of fixed 100 tokens
```

## Page Filtering (Needs Implementation)

### Image-Only Page Detection
```python
# Proposed implementation:
def is_image_only_page(page_text: str, word_count: int) -> bool:
    """Detect pages that are primarily images."""
    if word_count < 5:  # Very few words
        return True
    
    char_to_word_ratio = len(page_text) / max(word_count, 1)
    if char_to_word_ratio < 3:  # Very short words (OCR artifacts)
        return True
        
    return False
```

### Noise Filtering
```python
# Current basic filtering in chunk creation:
noise_patterns = [
    r"intentionally left blank",
    r"this page.*blank",
    r"^\s*\d+\s*$",  # Page numbers only
]

def is_noise_content(text: str) -> bool:
    """Filter out obvious noise content."""
    text_lower = text.lower().strip()
    
    if len(text_lower) < 20:  # Too short
        return True
        
    for pattern in noise_patterns:
        if re.search(pattern, text_lower):
            return True
            
    return False
```

## Metadata Schema

### File-Level Metadata
```json
{
  "doc_id": "sha256_hash_of_path",
  "relative_path": "subfolder/document.pdf",
  "content_hash": "sha256_content_hash",
  "file_name": "document.pdf",
  "file_size": 1048576,
  "mtime": 1703123456.789
}
```

### Page-Level Metadata (PDFs)
```json
{
  "page": 3,
  "total_pages": 45,
  "source_type": "pdf_page",
  "has_tables": true,
  "table_count": 2
}
```

### Chunk-Level Metadata
```json
{
  "chunk_index": 0,
  "chunk_hash": "sha256_chunk_hash",
  "token_count": 785,
  "char_count": 3140
}
```

## Environment Configuration Application

### Current Config (indexer/__init__.py)
```python
CONFIG = {
    "WATCH_DIR": os.getenv("LEXA_WATCH_DIR", "Database"),
    "CACHE_DIR": os.getenv("LEXA_CACHE_DIR", "Database/.lexa-cache"),
    "ALLOWED_EXT": {".pdf", ".docx", ".txt", ".md"},  # Needs expansion
    "CHUNK_TOKENS": int(os.getenv("LEXA_CHUNK_TOKENS", "800")),
    "OCR_WORD_THRESHOLD": int(os.getenv("LEXA_OCR_WORD_THRESHOLD", "50")),
    "EMBED_MODEL": os.getenv("LEXA_EMBED_MODEL", "text-embedding-3-large"),
}
```

### Required Updates
```python
# Should add these flags:
"DISABLE_OCR": bool(os.getenv("LEXA_DISABLE_OCR", "0") == "1"),
"DISABLE_TABLES": bool(os.getenv("LEXA_DISABLE_TABLES", "0") == "1"),
"SKIP_IMAGE_ONLY": bool(os.getenv("LEXA_SKIP_IMAGE_ONLY", "0") == "1"),
"CHUNK_CHARS": int(os.getenv("LEXA_CHUNK_CHARS", "1200")),
"CHUNK_OVERLAP": float(os.getenv("LEXA_CHUNK_OVERLAP", "0.25")),
"ALLOWED_EXT": set(os.getenv("LEXA_EXTS", ".pdf,.docx,.doc,.pptx,.ppt,.txt,.md,.rtf,.xlsx,.xls,.csv").split(",")),
```

## Spreadsheet Processing (Needs Implementation)

### Excel/CSV Flattening
```python
def process_spreadsheet(file_path: str) -> str:
    """Convert spreadsheet to text format."""
    import pandas as pd
    
    # Read all sheets
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        sheets = {'Sheet1': df}
    else:
        sheets = pd.read_excel(file_path, sheet_name=None)
    
    text_content = []
    for sheet_name, df in sheets.items():
        text_content.append(f"Sheet: {sheet_name}\n")
        text_content.append(df.to_string(index=False))
        text_content.append("\n\n")
    
    return "".join(text_content)
```

## Header/Footer Detection & Deduplication

### Proposed Implementation
```python
def detect_headers_footers(pages_text: List[str]) -> Dict[str, str]:
    """Detect repeating headers/footers across pages."""
    # Find common text at start/end of pages
    common_headers = []
    common_footers = []
    
    for page_text in pages_text:
        lines = page_text.split('\n')
        if len(lines) > 2:
            common_headers.append(lines[0][:100])  # First line
            common_footers.append(lines[-1][:100])  # Last line
    
    # Find most common patterns
    from collections import Counter
    header_counts = Counter(common_headers)
    footer_counts = Counter(common_footers)
    
    return {
        'header': header_counts.most_common(1)[0][0] if header_counts else '',
        'footer': footer_counts.most_common(1)[0][0] if footer_counts else ''
    }

def clean_page_text(text: str, header: str, footer: str) -> str:
    """Remove detected headers/footers from page text."""
    if header and text.startswith(header):
        text = text[len(header):].lstrip()
    if footer and text.endswith(footer):
        text = text[:-len(footer)].rstrip()
    return text
```

## Performance Optimizations

### Caching Strategy
- **OCR Results**: Cached per page with content hash
- **Table Extractions**: Cached separately from OCR
- **Document Metadata**: Cached to avoid reprocessing
- **Cache Invalidation**: Based on file modification time + content hash

### Concurrency
- **File Processing**: Single-threaded (I/O bound)
- **Embedding Generation**: Batched API calls
- **Database Operations**: Chunked upserts for large documents