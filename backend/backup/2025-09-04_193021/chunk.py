"""
Token-aware chunking with metadata preservation.
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
import re

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from . import CONFIG

logger = logging.getLogger(__name__)


class ChunkProcessor:
    def __init__(self):
        self.chunk_tokens = CONFIG["CHUNK_TOKENS"]

        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
                logger.info("Using tiktoken for precise token counting")
            except Exception as e:
                logger.warning(f"Failed to initialize tiktoken: {e}")
                self.tokenizer = None
        else:
            self.tokenizer = None
            logger.info("Using character-based approximation for chunking")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or approximation."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough approximation: 4 characters per token
            return len(text) // 4

    def chunk_text(
        self, text: str, base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        Preserves page boundaries and adds chunk-specific metadata.
        """
        if not text.strip():
            return []

        chunks = []

        # Split into sentences for better chunk boundaries
        sentences = self._split_sentences(text)

        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        overlap_tokens = 100  # Fixed overlap

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If adding this sentence would exceed the limit, finalize current chunk
            if current_tokens + sentence_tokens > self.chunk_tokens and current_chunk:
                chunk_data = self._create_chunk(
                    current_chunk.strip(), base_metadata, chunk_index
                )
                chunks.append(chunk_data)

                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk, overlap_tokens)
                current_chunk = overlap_text + sentence
                current_tokens = self.count_tokens(current_chunk)
                chunk_index += 1
            else:
                current_chunk += sentence
                current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk.strip():
            chunk_data = self._create_chunk(
                current_chunk.strip(), base_metadata, chunk_index
            )
            chunks.append(chunk_data)

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - could be enhanced with nltk
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s + " " for s in sentences if s.strip()]

    def _get_overlap(self, text: str, overlap_tokens: int) -> str:
        """Get overlap text from the end of current chunk."""
        if overlap_tokens <= 0:
            return ""

        words = text.split()
        if not words:
            return ""

        # Approximate overlap by taking last N words
        overlap_words = int(overlap_tokens * 0.75)  # Rough conversion
        overlap_words = min(overlap_words, len(words))

        return " ".join(words[-overlap_words:]) + " "

    def _create_chunk(
        self, text: str, base_metadata: Dict[str, Any], chunk_index: int
    ) -> Dict[str, Any]:
        """Create chunk dictionary with full metadata."""
        chunk_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

        return {
            "text": text,
            "metadata": {
                **base_metadata,
                "chunk_index": chunk_index,
                "chunk_hash": chunk_hash,
                "token_count": self.count_tokens(text),
                "char_count": len(text),
            },
        }


# Global chunk processor instance
chunk_processor = ChunkProcessor()
