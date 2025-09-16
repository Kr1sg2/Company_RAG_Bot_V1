"""
ChromaDB document storage interface.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Set
from uuid import uuid4

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# Try the new config object first; fall back to env/defaults if not available
try:
    from .config import CONFIG as _OBJ_CONFIG  # IndexerConfig
except Exception:
    _OBJ_CONFIG = None


def _chroma_path() -> str:
    if _OBJ_CONFIG is not None and hasattr(_OBJ_CONFIG, "CHROMA_PATH"):
        return _OBJ_CONFIG.CHROMA_PATH
    return os.getenv("LEXA_CHROMA_PATH", "chroma_db")


def _collection_name(default: str = "lexa_documents") -> str:
    # If you later add a name into CONFIG, read it here; otherwise keep default
    try:
        if _OBJ_CONFIG is not None and hasattr(_OBJ_CONFIG, "COLLECTION_NAME"):
            return getattr(_OBJ_CONFIG, "COLLECTION_NAME") or default
    except Exception:
        pass
    return default


class DocumentStore:
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or _collection_name("lexa_documents")

        try:
            self.client = chromadb.PersistentClient(
                path=_chroma_path(),
                settings=Settings(anonymized_telemetry=False)
            )

            # Keep same HNSW metric as before
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            logger.info(f"Connected to ChromaDB collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    # ---------- NEW: wipe/reset helpers ----------

    def wipe_collection(self, recreate: bool = True) -> None:
        """
        Drop the entire collection (all vectors/chunks). If `recreate` is True,
        immediately create a fresh empty collection with the same name/metadata,
        and attach it back to this store instance.
        """
        try:
            name = self.collection_name or "lexa_documents"
            try:
                self.client.delete_collection(name)
                logger.info(f"Deleted Chroma collection: {name}")
            except Exception as e:
                # It's okay if it doesn't exist; we continue
                logger.warning(f"delete_collection({name}) raised: {e} (continuing)")

            if recreate:
                self.collection = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Recreated empty collection: {name}")
            else:
                self.collection = None
        except Exception as e:
            logger.error(f"Failed to wipe/reset collection: {e}")
            raise

    def reset_collection(self) -> None:
        """Alias for wipe_collection(recreate=True)."""
        self.wipe_collection(recreate=True)

    # ---------- Existing APIs ----------

    def get_existing_doc_ids(self) -> Set[str]:
        """Get all document IDs currently in the store."""
        try:
            results = self.collection.get(include=["metadatas"])
            doc_ids = set()

            for metadata in results["metadatas"]:
                if metadata and "doc_id" in metadata:
                    doc_ids.add(metadata["doc_id"])

            logger.debug(f"Found {len(doc_ids)} existing documents")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to get existing doc IDs: {e}")
            return set()

    def get_doc_chunk_ids(self, doc_id: str) -> List[str]:
        """Get all chunk IDs for a specific document."""
        try:
            results = self.collection.get(
                where={"doc_id": doc_id},
                include=["metadatas"]
            )

            chunk_ids = []
            for i, metadata in enumerate(results["metadatas"]):
                if metadata:
                    chunk_ids.append(results["ids"][i])

            logger.debug(f"Found {len(chunk_ids)} chunks for doc {doc_id}")
            return chunk_ids

        except Exception as e:
            logger.error(f"Failed to get chunk IDs for doc {doc_id}: {e}")
            return []

    def upsert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Insert or update document chunks with embeddings."""
        if not chunks or not embeddings:
            return

        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        try:
            ids = []
            texts = []
            metadatas = []

            for chunk, embedding in zip(chunks, embeddings):
                # Generate unique chunk ID
                chunk_id = str(uuid4())
                ids.append(chunk_id)
                texts.append(chunk["text"])
                metadatas.append(chunk["metadata"])

            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Upserted {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise

    def delete_document(self, doc_id: str) -> int:
        """Delete all chunks for a document. Returns number of chunks deleted."""
        try:
            chunk_ids = self.get_doc_chunk_ids(doc_id)

            if not chunk_ids:
                logger.debug(f"No chunks found for doc {doc_id}")
                return 0

            self.collection.delete(ids=chunk_ids)

            logger.info(f"Deleted {len(chunk_ids)} chunks for doc {doc_id}")
            return len(chunk_ids)

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return 0

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where_filter: Optional[Dict] = None
    ) -> Dict[str, List]:
        """Search for similar chunks using vector similarity."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            doc_ids = self.get_existing_doc_ids()

            return {
                "total_chunks": count,
                "total_documents": len(doc_ids),
                "collection_name": self.collection_name
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "collection_name": self.collection_name
            }


# Global store instance
document_store = DocumentStore()

