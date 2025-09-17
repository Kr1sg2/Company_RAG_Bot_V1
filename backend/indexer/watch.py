# indexer/watch.py
import os
import time
import threading
import logging
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from . import CONFIG
from .pipeline import document_pipeline

logger = logging.getLogger(__name__)


class DocumentHandler(FileSystemEventHandler):
    def __init__(self, watch_dir: str):
        super().__init__()
        self.watch_dir = watch_dir
        self.debounce_seconds = int(os.getenv("LEXA_DEBOUNCE_SECONDS", "5"))
        self.processing_lock = threading.Lock()
        self.processing_files = {}  # path -> first_seen_ts
        self.stop_event = threading.Event()
        self.housekeeper = threading.Thread(target=self._housekeep_loop, daemon=True)
        logger.info(f"Ignored directories: {CONFIG['IGNORE_DIRS']}")
        self.housekeeper.start()

    def _should_ignore(self, file_path: str) -> bool:
        rel = os.path.relpath(file_path, self.watch_dir)
        parts = rel.split(os.sep)
        if any(p in CONFIG["IGNORE_DIRS"] for p in parts):
            return True
        if os.path.basename(file_path).startswith("."):
            return True
        ext = Path(file_path).suffix.lower()
        return ext not in CONFIG["ALLOWED_EXT"]

    def _housekeep_loop(self):
        while not self.stop_event.is_set():
            # take a snapshot (don't hold lock while sleeping)
            with self.processing_lock:
                snapshot = list(self.processing_files.items())

            to_process = []
            for path, first_seen in snapshot:
                if not os.path.exists(path):
                    with self.processing_lock:
                        self.processing_files.pop(path, None)
                    continue
                try:
                    size1 = os.path.getsize(path)
                    time.sleep(0.5)
                    size2 = os.path.getsize(path)
                except Exception:
                    continue
                stable = (size1 == size2) and (
                    (time.time() - first_seen) >= self.debounce_seconds
                )
                if stable:
                    to_process.append(path)
                    with self.processing_lock:
                        self.processing_files.pop(path, None)

            for path in to_process:
                try:
                    logger.info(
                        f"Processing stable file: {os.path.relpath(path, self.watch_dir)}"
                    )
                    document_pipeline.process_document(path, self.watch_dir)
                except Exception as e:
                    logger.error(f"Processing failed for {path}: {e}")

            time.sleep(0.5)

    def _delete_file(self, file_path: str):
        try:
            logger.info(
                f"Deleting from index: {os.path.relpath(file_path, self.watch_dir)}"
            )
            document_pipeline.delete_document(file_path, self.watch_dir)
        except Exception as e:
            logger.error(f"Delete failed for {file_path}: {e}")

    def on_created(self, event):
        if event.is_directory:
            return
        file_path = event.src_path  # FIXED
        if self._should_ignore(file_path):
            return
        logger.debug(f"File created: {os.path.relpath(file_path, self.watch_dir)}")
        with self.processing_lock:
            self.processing_files[file_path] = time.time()

    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = event.src_path  # FIXED
        if self._should_ignore(file_path):
            return
        logger.debug(f"File modified: {os.path.relpath(file_path, self.watch_dir)}")
        with self.processing_lock:
            self.processing_files[file_path] = time.time()

    def on_deleted(self, event):
        if event.is_directory:
            return
        file_path = event.src_path  # FIXED
        if self._should_ignore(file_path):
            return
        logger.info(f"File deleted: {os.path.relpath(file_path, self.watch_dir)}")
        self._delete_file(file_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        src_path = event.src_path
        dest_path = event.dest_path
        if not self._should_ignore(src_path):
            logger.info(f"File moved from: {os.path.relpath(src_path, self.watch_dir)}")
            self._delete_file(src_path)
        if not self._should_ignore(dest_path) and os.path.exists(dest_path):
            logger.info(f"File moved to: {os.path.relpath(dest_path, self.watch_dir)}")
            with self.processing_lock:
                self.processing_files[dest_path] = time.time()

    def stop(self):
        self.stop_event.set()
        if hasattr(self, "housekeeper"):
            self.housekeeper.join(timeout=5)


class DocumentWatcher:
    def __init__(self, watch_dir: str = None):
        self.watch_dir = watch_dir or CONFIG["WATCH_DIR"]
        self.observer = None
        self.handler = None
        logger.info(f"Document watcher initialized for: {self.watch_dir}")

    def start(self):
        if not os.path.exists(self.watch_dir):
            logger.error(f"Watch directory does not exist: {self.watch_dir}")
            return False
        try:
            self.handler = DocumentHandler(self.watch_dir)
            from watchdog.observers import Observer

            self.observer = Observer()
            self.observer.schedule(self.handler, self.watch_dir, recursive=True)
            self.observer.start()
            logger.info(f"Started watching directory: {self.watch_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to start watcher: {e}")
            return False

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        if self.handler:
            self.handler.stop()
        logger.info("Document watcher stopped")

    def run(self):
        if not self.start():
            return
        try:
            logger.info("Document watcher running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()


if __name__ == "__main__":
    watcher = DocumentWatcher()
    watcher.run()
