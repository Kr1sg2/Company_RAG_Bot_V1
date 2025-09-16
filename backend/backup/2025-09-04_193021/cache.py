"""
Cache management for OCR results and table extractions.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from . import CONFIG

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or CONFIG['CACHE_DIR']
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_doc_cache_dir(self, doc_id: str) -> str:
        """Get cache directory for a specific document."""
        doc_cache_dir = os.path.join(self.cache_dir, doc_id)
        os.makedirs(doc_cache_dir, exist_ok=True)
        return doc_cache_dir
        
    def save_doc_meta(self, doc_id: str, meta: Dict[str, Any]) -> None:
        """Save document metadata."""
        cache_dir = self.get_doc_cache_dir(doc_id)
        meta_path = os.path.join(cache_dir, 'doc.meta.json')
        
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        logger.debug(f"Saved metadata for {doc_id}")
        
    def load_doc_meta(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Load document metadata."""
        cache_dir = self.get_doc_cache_dir(doc_id)
        meta_path = os.path.join(cache_dir, 'doc.meta.json')
        
        if not os.path.exists(meta_path):
            return None
            
        try:
            with open(meta_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata for {doc_id}: {e}")
            return None
            
    def save_page_ocr(self, doc_id: str, page_num: int, ocr_text: str) -> None:
        """Save OCR text for a page."""
        cache_dir = self.get_doc_cache_dir(doc_id)
        ocr_path = os.path.join(cache_dir, f'page-{page_num:04d}.ocr.txt')
        
        with open(ocr_path, 'w', encoding='utf-8') as f:
            f.write(ocr_text)
        logger.debug(f"Saved OCR for {doc_id} page {page_num}")
        
    def load_page_ocr(self, doc_id: str, page_num: int) -> Optional[str]:
        """Load OCR text for a page."""
        cache_dir = self.get_doc_cache_dir(doc_id)
        ocr_path = os.path.join(cache_dir, f'page-{page_num:04d}.ocr.txt')
        
        if not os.path.exists(ocr_path):
            return None
            
        try:
            with open(ocr_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to load OCR for {doc_id} page {page_num}: {e}")
            return None
            
    def save_page_tables(self, doc_id: str, page_num: int, tables: List[Dict]) -> None:
        """Save extracted tables for a page."""
        cache_dir = self.get_doc_cache_dir(doc_id)
        tables_path = os.path.join(cache_dir, f'page-{page_num:04d}.tables.json')
        
        with open(tables_path, 'w') as f:
            json.dump(tables, f, indent=2)
        logger.debug(f"Saved {len(tables)} tables for {doc_id} page {page_num}")
        
    def load_page_tables(self, doc_id: str, page_num: int) -> Optional[List[Dict]]:
        """Load extracted tables for a page."""
        cache_dir = self.get_doc_cache_dir(doc_id)
        tables_path = os.path.join(cache_dir, f'page-{page_num:04d}.tables.json')
        
        if not os.path.exists(tables_path):
            return None
            
        try:
            with open(tables_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load tables for {doc_id} page {page_num}: {e}")
            return None
            
    def delete_doc_cache(self, doc_id: str) -> None:
        """Delete all cached data for a document."""
        cache_dir = self.get_doc_cache_dir(doc_id)
        
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)
            logger.info(f"Deleted cache for {doc_id}")
            
    def has_cached_data(self, doc_id: str, content_hash: str) -> bool:
        """Check if document has valid cached data."""
        meta = self.load_doc_meta(doc_id)
        if not meta:
            return False
            
        return meta.get('content_hash') == content_hash