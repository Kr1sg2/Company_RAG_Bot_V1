"""
File and content hashing utilities for stable document IDs.
"""

import hashlib
import os
from pathlib import Path
from typing import Tuple

def compute_content_hash(file_path: str) -> str:
    """Compute SHA256 hash of file contents."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_doc_id(relative_path: str, content_hash: str) -> str:
    """Compute stable document ID from relative path and content hash."""
    combined = f"{relative_path}:{content_hash}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def get_relative_path(file_path: str, watch_dir: str) -> str:
    """Get relative path from watch directory."""
    return os.path.relpath(file_path, watch_dir)

def get_file_info(file_path: str, watch_dir: str) -> Tuple[str, str, str, float]:
    """
    Get file information for indexing.
    Returns: (relative_path, content_hash, doc_id, mtime)
    """
    relative_path = get_relative_path(file_path, watch_dir)
    content_hash = compute_content_hash(file_path)
    doc_id = compute_doc_id(relative_path, content_hash)
    mtime = os.path.getmtime(file_path)
    
    return relative_path, content_hash, doc_id, mtime