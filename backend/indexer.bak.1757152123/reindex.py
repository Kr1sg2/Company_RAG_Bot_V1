# indexer/reindex.py
"""
CLI tool for manual reindexing of documents.

Highlights
- Full wipe options:
    --wipe           Delete the entire Chroma collection (index)
    --wipe-cache     Delete the on-disk cache directory
    --wipe-all       Do both of the above
    --force          Skip confirmation prompts
- Backward-compatible config access whether CONFIG is a dict (indexer/__init__.py)
  or an object (indexer/config.py::IndexerConfig).
- Robust extension filtering: accepts values with or without leading dots.
- Simple list/delete utilities to inspect or remove specific documents.

Usage
    python -m indexer.reindex --wipe-all --force
    python -m indexer.reindex                      # full reindex of WATCH_DIR
    python -m indexer.reindex /path/to/file.pdf    # reindex a single file
    python -m indexer.reindex --list               # show index stats
    python -m indexer.reindex --delete DOC_ID      # delete by internal doc_id
"""

import os
import sys
import shutil
import logging
import argparse
from pathlib import Path

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Pipeline & store imports with robust fallbacks
# -----------------------------------------------------------------------------
pipeline = None
try:
    # Preferred: a module-level instance exported by pipeline.py
    from .pipeline import document_pipeline as _document_pipeline  # type: ignore
    pipeline = _document_pipeline
except Exception:
    try:
        # Newer class name
        from .pipeline import EnhancedDocumentPipeline  # type: ignore
        pipeline = EnhancedDocumentPipeline()
    except Exception:
        try:
            # Legacy class name
            from .pipeline import DocumentPipeline  # type: ignore
            pipeline = DocumentPipeline()
        except Exception as e:
            raise RuntimeError(
                "Unable to import a usable document pipeline from indexer.pipeline. "
                "Expected one of: `document_pipeline`, `EnhancedDocumentPipeline`, `DocumentPipeline`."
            ) from e

# Store (expects .client, .collection_name and helpers used below)
from .store import document_store as doc_store  # has .client and .collection_name  # noqa

# -----------------------------------------------------------------------------
# Config (support both legacy dict and new object)
# -----------------------------------------------------------------------------
try:
    from .config import CONFIG as _OBJ_CONFIG  # new style object with attributes
    _DICT_CONFIG = None
except Exception:
    _OBJ_CONFIG = None
    try:
        from . import CONFIG as _DICT_CONFIG   # legacy dict-style CONFIG
    except Exception:
        _DICT_CONFIG = None


def _cfg(name: str, default=None):
    """Get config value from object CONFIG or legacy dict CONFIG."""
    if _OBJ_CONFIG is not None and hasattr(_OBJ_CONFIG, name):
        return getattr(_OBJ_CONFIG, name)
    if _DICT_CONFIG is not None and isinstance(_DICT_CONFIG, dict) and name in _DICT_CONFIG:
        return _DICT_CONFIG[name]
    return default


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _allowed_ext_set():
    """Normalize allowed extensions to support both '.pdf' and 'pdf' entries."""
    raw = _cfg("ALLOWED_EXT", {".pdf", ".docx", ".txt", ".md"})
    out = set()
    for ext in raw:
        e = str(ext).strip().lower()
        if not e:
            continue
        if not e.startswith("."):
            out.add("." + e)
        out.add(e)
    return out


def _is_allowed_file(path: str) -> bool:
    """Check file extension against normalized allow-list."""
    ext = Path(path).suffix.lower()
    return ext in _allowed_ext_set()


def _ignored_dirnames():
    return _cfg("IGNORE_DIRS", {".lexa-cache", "__pycache__", ".git"})


def _watch_dir():
    return _cfg("WATCH_DIR", "Database")


def _cache_dir():
    # Prefer explicit cache dir; fallback to WATCH_DIR/.lexa-cache
    explicit = _cfg("CACHE_DIR", None)
    if explicit:
        return explicit
    return os.path.join(_watch_dir(), ".lexa-cache")


def _confirm_or_abort(prompt: str, force: bool):
    if force:
        return
    ans = input(f"{prompt} Type 'yes' to continue: ").strip().lower()
    if ans != "yes":
        print("Aborted.")
        sys.exit(1)


# -----------------------------------------------------------------------------
# Wipe utilities
# -----------------------------------------------------------------------------
def wipe_index(force: bool = False):
    """
    Drop and recreate the entire Chroma collection.
    Uses document_store.client and document_store.collection_name.
    """
    try:
        name = getattr(doc_store, "collection_name", None) or "lexa_documents"
        _confirm_or_abort(f"This will DELETE the entire index collection '{name}'.", force)
        # Delete the collection if it exists, ignore if not
        try:
            doc_store.client.delete_collection(name)
            logger.info(f"Deleted collection: {name}")
        except Exception as e:
            logger.warning(f"delete_collection({name}) raised: {e} (continuing)")

        # Recreate a fresh, empty collection and reattach to the store instance
        doc_store.collection = doc_store.client.get_or_create_collection(name)
        logger.info(f"Recreated empty collection: {name}")
    except Exception as e:
        logger.error(f"Failed to wipe index: {e}")
        raise


def wipe_cache(force: bool = False):
    """Delete the entire on-disk cache directory and recreate it."""
    path = _cache_dir()
    _confirm_or_abort(f"This will DELETE the cache directory at '{path}'.", force)
    try:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path, exist_ok=True)
        logger.info(f"Recreated cache directory: {path}")
    except Exception as e:
        logger.error(f"Failed to wipe cache '{path}': {e}")
        raise


# -----------------------------------------------------------------------------
# Reindex logic
# -----------------------------------------------------------------------------
def reindex_file(file_path: str, watch_dir: str) -> bool:
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    if not _is_allowed_file(file_path):
        logger.error(f"Unsupported file type: {Path(file_path).suffix.lower()}")
        return False
    logger.info(f"Reindexing: {os.path.relpath(file_path, watch_dir)}")
    return pipeline.process_document(file_path, watch_dir)


def reindex_directory(dir_path: str, watch_dir: str) -> int:
    success_count = 0
    for root, dirs, files in os.walk(dir_path):
        # prune ignored dirs
        dirs[:] = [d for d in dirs if d not in _ignored_dirnames() and not d.startswith(".")]
        for file in files:
            if file.startswith("."):
                continue
            file_path = os.path.join(root, file)
            if _is_allowed_file(file_path):
                if reindex_file(file_path, watch_dir):
                    success_count += 1
    return success_count


def full_reindex(watch_dir: str) -> int:
    logger.info(f"Starting full reindex of: {watch_dir}")
    if not os.path.exists(watch_dir):
        logger.error(f"Watch directory does not exist: {watch_dir}")
        return 0
    return reindex_directory(watch_dir, watch_dir)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Reindex documents for Lexa")
    parser.add_argument("path", nargs="?", help="Path to file or directory to reindex (default: full reindex)")
    parser.add_argument("--watch-dir", help="Override watch directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    # Utilities
    parser.add_argument("--list", action="store_true", help="List index stats and a few doc IDs")
    parser.add_argument("--delete", help="Delete document by doc_id")

    # Wipe options
    parser.add_argument("--wipe", action="store_true", help="Delete the entire vector index collection")
    parser.add_argument("--wipe-cache", action="store_true", help="Delete the cache directory")
    parser.add_argument("--wipe-all", action="store_true", help="Delete BOTH index collection and cache directory")
    parser.add_argument("--force", action="store_true", help="Do not prompt for confirmation when wiping")

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    watch_dir = args.watch_dir or _watch_dir()

    try:
        # Wipe paths first if requested
        if args.wipe_all or args.wipe:
            wipe_index(force=args.force)
        if args.wipe_all or args.wipe_cache:
            wipe_cache(force=args.force)
        if args.wipe_all or args.wipe or args.wipe_cache:
            # If wipe was requested without any reindex path, we're done.
            if not args.path and not args.list and not args.delete:
                print("Wipe completed.")
                return 0

        if args.list:
            doc_ids = doc_store.get_existing_doc_ids()
            if not doc_ids:
                print("No documents in index.")
            else:
                print(f"Found {len(doc_ids)} indexed documents:")
                stats = doc_store.get_collection_stats()
                print(f"Total chunks: {stats['total_chunks']}")
                for doc_id in list(doc_ids)[:10]:  # Show first 10
                    chunks = doc_store.get_doc_chunk_ids(doc_id)
                    print(f"  {doc_id[:32]}... (chunks: {len(chunks)})")
                if len(doc_ids) > 10:
                    print(f"  ... and {len(doc_ids) - 10} more documents")
            return 0

        if args.delete:
            # Treat args.delete as an internal document ID
            deleted = doc_store.delete_document(args.delete)
            if deleted > 0:
                print(f"Deleted: {args.delete} ({deleted} chunks)")
            else:
                print(f"Document not found: {args.delete}")
            return 0

        # Reindex targets
        target = args.path or watch_dir
        if os.path.isdir(target):
            count = reindex_directory(target, watch_dir)
            print(f"Reindexed {count} files from {os.path.relpath(target, watch_dir) if target != watch_dir else target}")
            return 0
        elif os.path.isfile(target):
            ok = reindex_file(target, watch_dir)
            print("Reindex OK" if ok else "Reindex failed")
            return 0
        else:
            logger.error(f"Path not found: {target}")
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

