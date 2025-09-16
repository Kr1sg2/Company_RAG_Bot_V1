# indexer/chunk_fixed.py
import re
from typing import List, Dict, Any
from .config import CONFIG

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
    if not page_text or not page_text.strip():
        return []
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

