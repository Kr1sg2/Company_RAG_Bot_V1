# indexer/__init__.py
import os

CONFIG = {
    "WATCH_DIR": os.getenv("LEXA_WATCH_DIR", "Database"),
    "CACHE_DIR": os.getenv("LEXA_CACHE_DIR", "Database/.lexa-cache"),
    "ALLOWED_EXT": {".pdf", ".docx", ".txt", ".md"},
    "IGNORE_DIRS": {".lexa-cache", "__pycache__"},
    "CHUNK_TOKENS": int(os.getenv("LEXA_CHUNK_TOKENS", "800")),
    "OCR_WORD_THRESHOLD": int(os.getenv("LEXA_OCR_WORD_THRESHOLD", "50")),
    "EMBED_MODEL": os.getenv("LEXA_EMBED_MODEL", "text-embedding-3-large"),
}