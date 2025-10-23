"""
Enhanced Retrieval System for Hybrid AI
Combines vector similarity with BM25 keyword search and reranking
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result with content and metadata"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]
    
    
@dataclass
class RetrievalConfig:
    """Configuration for enhanced retrieval"""
    vector_weight: float = 0.7           # Weight for vector similarity
    bm25_weight: float = 0.3            # Weight for BM25 keyword search  
    max_results: int = 10               # Max results before reranking
    rerank_top_k: int = 5               # Results to return after reranking
    min_similarity_threshold: float = 0.1  # Minimum similarity to include
    

class EnhancedRetriever:
    """
    Hybrid retrieval combining vector search with BM25 and reranking
    """
    
    def __init__(self, config: RetrievalConfig = None):
        self.config = config or RetrievalConfig()
        self.bm25_index = None
        self._setup_bm25()
    
    def _setup_bm25(self) -> None:
        """Initialize BM25 index for keyword search"""
        try:
            from rank_bm25 import BM25Okapi
            self._BM25Okapi = BM25Okapi
            logger.info("BM25 index initialized successfully")
        except ImportError:
            logger.warning("rank_bm25 not available. Install with: pip install rank-bm25")
            self._BM25Okapi = None
    
    async def hybrid_search(
        self, 
        query: str,
        vector_store,  # ChromaDB collection
        query_embedding: List[float] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector similarity and BM25
        """
        # 1. Vector similarity search
        vector_results = await self._vector_search(query, vector_store, query_embedding)
        
        # 2. BM25 keyword search (if available)
        bm25_results = await self._bm25_search(query, vector_store)
        
        # 3. Combine and rerank results
        combined_results = self._combine_results(vector_results, bm25_results)
        
        # 4. Apply reranking
        final_results = self._rerank_results(query, combined_results)
        
        logger.info(f"Hybrid search returned {len(final_results)} results for query")
        return final_results
    
    async def _vector_search(
        self, 
        query: str, 
        vector_store, 
        query_embedding: List[float] = None
    ) -> List[SearchResult]:
        """Perform vector similarity search"""
        try:
            # Use provided embedding or generate one
            if query_embedding:
                results = vector_store.query(
                    query_embeddings=[query_embedding],
                    n_results=self.config.max_results
                )
            else:
                results = vector_store.query(
                    query_texts=[query],
                    n_results=self.config.max_results
                )
            
            vector_results = []
            if results and 'documents' in results:
                documents = results['documents'][0] if results['documents'] else []
                distances = results['distances'][0] if results.get('distances') else [0] * len(documents)
                metadatas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(documents)
                
                for i, (doc, distance, metadata) in enumerate(zip(documents, distances, metadatas)):
                    # Convert distance to similarity score (assuming cosine distance)
                    similarity = 1.0 - distance
                    
                    if similarity >= self.config.min_similarity_threshold:
                        vector_results.append(SearchResult(
                            content=doc,
                            score=similarity * self.config.vector_weight,
                            source="vector_search",
                            metadata=metadata or {}
                        ))
            
            return vector_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _bm25_search(self, query: str, vector_store) -> List[SearchResult]:
        """Perform BM25 keyword search"""
        if not self._BM25Okapi:
            return []
        
        try:
            # Get all documents from vector store for BM25 indexing
            all_docs = await self._get_all_documents(vector_store)
            
            if not all_docs:
                return []
            
            # Tokenize documents for BM25
            tokenized_docs = [doc['content'].split() for doc in all_docs]
            
            # Create BM25 index
            bm25 = self._BM25Okapi(tokenized_docs)
            
            # Search
            query_tokens = query.split()
            bm25_scores = bm25.get_scores(query_tokens)
            
            # Convert to SearchResult objects
            bm25_results = []
            for i, (doc, score) in enumerate(zip(all_docs, bm25_scores)):
                if score > 0:  # Only include results with positive BM25 score
                    bm25_results.append(SearchResult(
                        content=doc['content'],
                        score=score * self.config.bm25_weight,
                        source="bm25_search",
                        metadata=doc.get('metadata', {})
                    ))
            
            # Sort by BM25 score
            bm25_results.sort(key=lambda x: x.score, reverse=True)
            return bm25_results[:self.config.max_results]
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    async def _get_all_documents(self, vector_store) -> List[Dict[str, Any]]:
        """Get all documents from vector store for BM25 indexing"""
        try:
            # Query with a large limit to get all documents
            results = vector_store.get()
            
            documents = []
            if results and 'documents' in results:
                docs = results['documents']
                metadatas = results.get('metadatas', [{}] * len(docs))
                
                for doc, metadata in zip(docs, metadatas):
                    documents.append({
                        'content': doc,
                        'metadata': metadata or {}
                    })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
    
    def _combine_results(
        self, 
        vector_results: List[SearchResult], 
        bm25_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Combine vector and BM25 results, handling duplicates"""
        combined = {}
        
        # Add vector results
        for result in vector_results:
            key = self._get_content_key(result.content)
            combined[key] = result
        
        # Add BM25 results, combining scores for duplicates
        for result in bm25_results:
            key = self._get_content_key(result.content)
            if key in combined:
                # Combine scores from both methods
                combined[key].score += result.score
                combined[key].source = "hybrid"
            else:
                combined[key] = result
        
        # Convert back to list and sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:self.config.max_results]
    
    def _get_content_key(self, content: str) -> str:
        """Generate a key for deduplication based on content"""
        # Use first 100 characters as key for deduplication
        return content[:100].strip().lower()
    
    def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Apply reranking to improve result quality"""
        if len(results) <= self.config.rerank_top_k:
            return results
        
        # Simple reranking based on query term overlap
        query_terms = set(query.lower().split())
        
        for result in results:
            content_terms = set(result.content.lower().split())
            overlap_ratio = len(query_terms.intersection(content_terms)) / len(query_terms)
            
            # Boost score based on term overlap
            result.score *= (1.0 + overlap_ratio * 0.2)
        
        # Re-sort and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:self.config.rerank_top_k]
    
    def format_context(self, results: List[SearchResult]) -> str:
        """Format search results into context for the AI model"""
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source_info = result.metadata.get('source', 'Unknown')
            context_parts.append(f"[Source {i}: {source_info}]\n{result.content}")
        
        return "\n\n".join(context_parts)
    
    def get_retrieval_stats(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Get statistics about the retrieval results"""
        if not results:
            return {"total_results": 0}
        
        sources = [r.source for r in results]
        return {
            "total_results": len(results),
            "vector_results": sources.count("vector_search"),
            "bm25_results": sources.count("bm25_search"),
            "hybrid_results": sources.count("hybrid"),
            "avg_score": np.mean([r.score for r in results]),
            "max_score": max([r.score for r in results]),
            "min_score": min([r.score for r in results])
        }