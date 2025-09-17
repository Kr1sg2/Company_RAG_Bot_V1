# indexer/chunk_fixed.py
import re
from typing import List, Dict, Any

CHUNK_CHARS = 1400
OVERLAP_CHARS = 250


def _split_paragraphs(text: str) -> List[str]:
    # keep headings as their own paragraphs
    parts = re.split(r"\n{2,}", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # join too-short lines that were hard-wrapped
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
            # start next window with overlap from previous tail
            tail = buf[-OVERLAP_CHARS:] if buf else ""
            buf = (tail + "\n" + p).strip()
    if buf:
        chunks.append({"text": buf, "metadata": meta})
    return chunks
