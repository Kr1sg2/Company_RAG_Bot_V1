# indexer/reindex.py
"""
CLI tool for manual reindexing of documents.
"""
import os, sys, logging, argparse
from pathlib import Path
from .pipeline import document_pipeline as pipeline
from .store import document_store as doc_store
from . import CONFIG

logger = logging.getLogger(__name__)


def reindex_file(file_path: str, watch_dir: str) -> bool:
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    ext = Path(file_path).suffix.lower()
    if ext not in CONFIG["ALLOWED_EXT"]:
        logger.error(f"Unsupported file type: {ext}")
        return False
    logger.info(f"Reindexing: {os.path.relpath(file_path, watch_dir)}")
    return pipeline.process_document(file_path, watch_dir)


def reindex_directory(dir_path: str, watch_dir: str) -> int:
    success_count = 0
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [
            d for d in dirs if d not in CONFIG["IGNORE_DIRS"] and not d.startswith(".")
        ]
        for file in files:
            if file.startswith("."):
                continue
            file_path = os.path.join(root, file)
            ext = Path(file_path).suffix.lower()
            if ext in CONFIG["ALLOWED_EXT"]:
                if reindex_file(file_path, watch_dir):
                    success_count += 1
    return success_count


def full_reindex(watch_dir: str) -> int:
    logger.info(f"Starting full reindex of: {watch_dir}")
    if not os.path.exists(watch_dir):
        logger.error(f"Watch directory does not exist: {watch_dir}")
        return 0
    return reindex_directory(watch_dir, watch_dir)


def main():
    parser = argparse.ArgumentParser(description="Reindex documents for Lexa")
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to file or directory to reindex (default: full reindex)",
    )
    parser.add_argument("--watch-dir", help="Override watch directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--list", action="store_true", help="List all indexed documents"
    )
    parser.add_argument("--delete", help="Delete document by relative path")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    watch_dir = args.watch_dir or CONFIG["WATCH_DIR"]
    try:
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
            # Treat args.delete as a document ID
            deleted = doc_store.delete_document(args.delete)
            if deleted > 0:
                print(f"Deleted: {args.delete} ({deleted} chunks)")
            else:
                print(f"Document not found: {args.delete}")
            return 0

        if args.path:
            target_path = os.path.abspath(args.path)
            if os.path.isfile(target_path):
                success = reindex_file(target_path, watch_dir)
                return 0 if success else 1
            elif os.path.isdir(target_path):
                count = reindex_directory(target_path, watch_dir)
                print(f"Reindexed {count} files")
                return 0
            else:
                logger.error(f"Path does not exist: {target_path}")
                return 1
        else:
            count = full_reindex(watch_dir)
            print(f"Reindexed {count} files")
            return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error during reindex: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
