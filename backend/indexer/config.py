"""
Centralized configuration management for indexer with environment variable support.
"""

import os


class IndexerConfig:
    """Centralized configuration for the indexing pipeline."""

    def __init__(self):
        # Core directories
        self.WATCH_DIR = os.getenv("LEXA_WATCH_DIR", "Database")
        self.CACHE_DIR = os.getenv("LEXA_CACHE_DIR", "Database/.lexa-cache")
        self.CHROMA_PATH = os.getenv("LEXA_CHROMA_PATH", "chroma_db")

        # Feature toggles
        self.DISABLE_OCR = os.getenv("LEXA_DISABLE_OCR", "0") == "1"
        self.DISABLE_TABLES = os.getenv("LEXA_DISABLE_TABLES", "0") == "1"
        self.SKIP_IMAGE_ONLY = os.getenv("LEXA_SKIP_IMAGE_ONLY", "0") == "1"

        # Chunking strategy
        self.CHUNK_CHARS = int(os.getenv("LEXA_CHUNK_CHARS", "1200"))
        self.CHUNK_OVERLAP = float(os.getenv("LEXA_CHUNK_OVERLAP", "0.25"))

        # File types
        extensions_str = os.getenv(
            "LEXA_EXTS", ".pdf,.docx,.doc,.pptx,.ppt,.txt,.md,.rtf,.xlsx,.xls,.csv"
        )
        self.ALLOWED_EXT = set(ext.strip() for ext in extensions_str.split(","))

        # OCR settings
        self.OCR_WORD_THRESHOLD = int(os.getenv("LEXA_OCR_WORD_THRESHOLD", "50"))

        # Embedding model
        self.EMBED_MODEL = os.getenv("LEXA_EMBED_MODEL", "text-embedding-3-large")

        # Smart chunking configuration
        self.USE_SMART_CHUNKING = os.getenv("USE_SMART_CHUNKING", "0") == "1"
        self.SMART_CHUNK_MIN_CHARS = int(os.getenv("SMART_CHUNK_MIN_CHARS", "180"))
        self.SMART_CHUNK_MAX_CHARS = int(os.getenv("SMART_CHUNK_MAX_CHARS", "1100"))
        self.SMART_CHUNK_OVERLAP_TOKENS = int(
            os.getenv("SMART_CHUNK_OVERLAP_TOKENS", "80")
        )
        self.SMART_CHUNK_MERGE_NEARBY = (
            os.getenv("SMART_CHUNK_MERGE_NEARBY", "1") == "1"
        )

        # Optional retrieval bias
        self.BIAS_BY_CHUNK_TYPE = os.getenv("BIAS_BY_CHUNK_TYPE", "0") == "1"

        # Ignored directories
        self.IGNORE_DIRS = {".lexa-cache", "__pycache__", ".git"}

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not os.path.exists(self.WATCH_DIR):
            errors.append(f"Watch directory does not exist: {self.WATCH_DIR}")

        if self.CHUNK_CHARS < 100:
            errors.append(f"CHUNK_CHARS too small: {self.CHUNK_CHARS} (minimum 100)")

        if not (0.0 <= self.CHUNK_OVERLAP <= 1.0):
            errors.append(
                f"CHUNK_OVERLAP must be between 0.0 and 1.0: {self.CHUNK_OVERLAP}"
            )

        if not self.ALLOWED_EXT:
            errors.append("No file extensions specified in LEXA_EXTS")

        return errors

    def log_settings(self) -> str:
        """Return configuration summary for logging."""
        return f"""Indexer Configuration:
  Watch Directory: {self.WATCH_DIR}
  Cache Directory: {self.CACHE_DIR}
  ChromaDB Path: {self.CHROMA_PATH}
  OCR Disabled: {self.DISABLE_OCR}
  Tables Disabled: {self.DISABLE_TABLES}
  Skip Image-Only: {self.SKIP_IMAGE_ONLY}
  Chunk Size: {self.CHUNK_CHARS} characters
  Chunk Overlap: {self.CHUNK_OVERLAP * 100}%
  Smart Chunking: {self.USE_SMART_CHUNKING}
  Allowed Extensions: {', '.join(sorted(self.ALLOWED_EXT))}
  Embedding Model: {self.EMBED_MODEL}"""


# Global configuration instance
CONFIG = IndexerConfig()
