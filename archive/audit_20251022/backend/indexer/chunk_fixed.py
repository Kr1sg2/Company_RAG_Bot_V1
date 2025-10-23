# indexer/chunk_fixed.py
import re
from typing import List, Dict, Any, Set
from pathlib import Path
from .config import CONFIG

# Track which PDFs have already been smart-chunked in this process
_SMART_CHUNKED_DOCS: Set[str] = set()

CHUNK_CHARS = CONFIG.CHUNK_CHARS
OVERLAP_CHARS = int(CONFIG.CHUNK_CHARS * CONFIG.CHUNK_OVERLAP)

def _split_paragraphs(text: str) -> List[str]:
    parts = re.split(r"\n{2,}", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        p = re.sub(r"([^\n])\n([^\n])", r"\1 \2", p)
        out.append(p)
    return out

def make_chunks(page_text: str, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Make chunks using smart chunking if enabled, otherwise use legacy method."""
    if not page_text or not page_text.strip():
        return []
    
    # Check if we should use smart chunking for PDFs
    if CONFIG.USE_SMART_CHUNKING and meta.get('file_path', '').endswith('.pdf'):
        try:
            from lexa_app.ingest.smart_chunker import smart_chunk
            file_path = meta.get('file_path')
            if file_path and Path(file_path).exists():
                # Prevent duplicating full-document chunks for each page
                if file_path in _SMART_CHUNKED_DOCS:
                    return []
                _SMART_CHUNKED_DOCS.add(file_path)
                
                smart_chunks = smart_chunk(file_path)
                
                # Convert smart chunks to legacy format
                converted_chunks = []
                for chunk_data in smart_chunks:
                    # Merge smart chunk metadata with existing metadata
                    merged_meta = {**meta, **chunk_data['metadata']}
                    converted_chunks.append({
                        'text': chunk_data['text'],
                        'metadata': merged_meta
                    })
                
                if converted_chunks:
                    return converted_chunks
            
        except Exception as e:
            print(f"Smart chunking failed for {meta.get('file_path', 'unknown')}, falling back to legacy: {e}")
            # Fall through to legacy chunking
    
    # Legacy chunking method
    paras = _split_paragraphs(page_text)
    buf = ""
    chunks = []
    for p in paras:
        if len(buf) + len(p) + 1 <= CHUNK_CHARS:
            buf = (buf + "\n" + p).strip()
        else:
            if buf:
                chunks.append({"text": buf, "metadata": meta})
            tail = buf[-OVERLAP_CHARS:] if buf else ""
            buf = (tail + "\n" + p).strip()
    if buf:
        chunks.append({"text": buf, "metadata": meta})
    return chunks

# Compatibility shim so existing pipeline code can call .chunk_text(...)
class _Compat:
    def chunk_text(self, text: str, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        return make_chunks(text, meta)

chunk_processor = _Compat()

