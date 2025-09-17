# app/retrieval.py
"""
Enhanced retrieval with BM25 re-ranking and answer guardrails.
"""
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import chromadb
from chromadb.config import Settings
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

# Remove global OpenAI import - will be imported lazily

logger = logging.getLogger(__name__)

class EnhancedRetriever:
    def __init__(self, chroma_path: str, collection_name: str = "lexa_documents"):
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.embed_model = os.getenv("LEXA_EMBED_MODEL", "text-embedding-3-large")
        
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        try:
            self.collection = self.client.get_collection(collection_name)
        except Exception:
            logger.warning(f"Collection {collection_name} not found, creating new one")
            self.collection = self.client.get_or_create_collection(collection_name)

        # Policy preferences (configurable)
        self.policy_keywords = ["handbook", "policy", "benefit", "hr", "procedure", "manual"]

    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for search query using same model as indexer."""
        # Lazy import so the app doesn't crash if OpenAI isn't present
        try:
            import openai  # type: ignore
        except Exception:
            logger.warning("OpenAI SDK not installed; falling back to query_texts mode")
            return None
            
        try:
            client = openai.OpenAI()
            response = client.embeddings.create(
                model=self.embed_model,
                input=[query]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return None

    def retrieve_with_rerank(self, query: str, top_k: int = 20, final_k: int = 3) -> List[Dict[str, Any]]:
        try:
            # Get query embedding using same model as indexer
            query_embedding = self.get_query_embedding(query)
            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=['documents', 'metadatas', 'distances']
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    include=['documents', 'metadatas', 'distances']
                )
            if not results['documents'][0]:
                logger.info("No documents found in vector search")
                return []

            candidates = []
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]

            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                try:
                    sim = max(0.0, min(1.0, 1.0 - float(distance)))
                except Exception:
                    sim = 0.0
                candidates.append({
                    'text': doc,
                    'metadata': metadata or {},
                    'vector_score': sim,
                    'vector_rank': i + 1
                })

            if BM25_AVAILABLE and len(candidates) > 1:
                candidates = self._apply_bm25_rerank(query, candidates)
            else:
                for c in candidates:
                    c['bm25_score'] = c['vector_score']
                    c['combined_score'] = c['vector_score']

            candidates = self._apply_policy_boost(candidates)
            candidates.sort(key=lambda x: x['combined_score'], reverse=True)
            return candidates[:final_k]

        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            return []

    def _apply_bm25_rerank(self, query: str, candidates: List[Dict]) -> List[Dict]:
        try:
            tokenized_docs = [re.findall(r'\b\w+\b', c['text'].lower()) for c in candidates]
            if not tokenized_docs:
                return candidates
            bm25 = BM25Okapi(tokenized_docs)
            query_tokens = re.findall(r'\b\w+\b', query.lower())
            bm25_scores = bm25.get_scores(query_tokens)
            max_bm25 = max(bm25_scores) if getattr(bm25_scores, "size", None) else 1.0
            for i, c in enumerate(candidates):
                c['bm25_score'] = (bm25_scores[i] / max_bm25) if max_bm25 > 0 else 0
                c['combined_score'] = (0.6 * c['vector_score'] + 0.4 * c['bm25_score'])
            return candidates
        except Exception as e:
            logger.error(f"BM25 re-ranking failed: {e}")
            for c in candidates:
                c['bm25_score'] = 0
                c['combined_score'] = c['vector_score']
            return candidates

    def _apply_policy_boost(self, candidates: List[Dict]) -> List[Dict]:
        for c in candidates:
            file_name = c['metadata'].get('file_name', '').lower()
            rel = c['metadata'].get('relative_path', '').lower()
            boost = 1.0
            for kw in self.policy_keywords:
                if kw in file_name or kw in rel:
                    boost = 1.2
                    break
            c['policy_boost'] = boost
            c['combined_score'] *= boost
        return candidates

    def check_numeric_consistency(self, query: str, candidates: List[Dict]) -> Tuple[bool, Optional[str]]:
        numeric_pattern = r'\b\d+(?:\.\d+)?\s*(?:days?|years?|months?|weeks?|hours?|%|percent|dollars?|\$)\b'
        if not re.search(r'\d', query):
            return True, None
        facts = []
        for c in candidates[:3]:
            text = c['text'].lower()
            numbers = re.findall(numeric_pattern, text, re.IGNORECASE)
            if numbers:
                facts.append({'numbers': numbers, 'file_name': c['metadata'].get('file_name', ''), 'policy_boost': c.get('policy_boost', 1.0)})
        if len(facts) < 2:
            return True, None
        all_nums = [n for f in facts for n in f['numbers']]
        if len(set(all_nums)) > 1:
            pol = [f for f in facts if f['policy_boost'] > 1.0]
            if pol:
                best = max(pol, key=lambda x: x['policy_boost'])
                return False, f"According to {best['file_name']}: {', '.join(best['numbers'])}"
        return True, None

    def format_answer_with_citations(self, query: str, candidates: List[Dict]) -> Dict[str, Any]:
        if not candidates:
            return {'answer': "I couldn't find relevant information in the documents.", 'sources': [], 'confidence': 0.0}
        is_consistent, authoritative = self.check_numeric_consistency(query, candidates)
        answer_parts, sources, seen = [], [], set()
        for c in candidates[:3]:
            md = c['metadata']
            file_name = md.get('file_name', 'Unknown')
            page = md.get('page', 1)
            key = f"{file_name}::{page}"
            if key in seen:
                continue
            seen.add(key)
            snippet = c['text'][:200].strip() + ("..." if len(c['text']) > 200 else "")
            answer_parts.append(snippet)
            sources.append({'file_name': file_name, 'page': page, 'confidence': c['combined_score']})
        answer = authoritative if authoritative else " ".join(answer_parts)
        labels = [f"{s['file_name']}, p. {s['page']}" if s['page'] > 1 else s['file_name'] for s in sources]
        citation_text = f" — {'; '.join(labels)}" if sources else ""
        return {'answer': answer + citation_text, 'sources': sources, 'confidence': candidates[0]['combined_score'], 'is_consistent': is_consistent}

def enhanced_search(query: str, chroma_path: Optional[str] = None) -> Dict[str, Any]:
    chroma_path = chroma_path or os.getenv("LEXA_CHROMA_PATH", "chroma_db")
    retriever = EnhancedRetriever(chroma_path)
    candidates = retriever.retrieve_with_rerank(query)
    return retriever.format_answer_with_citations(query, candidates)