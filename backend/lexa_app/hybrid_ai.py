"""
Hybrid AI Integration for Lexa AI
Integrates the hybrid provider system with the existing FastAPI backend
"""
import os
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from .providers import (
    OllamaProvider, 
    OpenAIProvider, 
    HybridRouter, 
    ProviderRequest, 
    ProviderResponse
)
from .providers.enhanced_retrieval import EnhancedRetriever, RetrievalConfig

logger = logging.getLogger(__name__)


class HybridAIService:
    """
    Main service class for hybrid AI functionality
    Integrates with existing Lexa AI backend
    """
    
    def __init__(self):
        self.router: Optional[HybridRouter] = None
        self.ollama_provider: Optional[OllamaProvider] = None
        self.openai_provider: Optional[OpenAIProvider] = None
        self.retriever: Optional[EnhancedRetriever] = None
        self.initialized = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the hybrid AI service"""
        try:
            if config is None:
                config = self._load_config_from_env()
            
            # Initialize enhanced retriever
            retrieval_config = RetrievalConfig(
                vector_weight=config.get("vector_weight", 0.7),
                bm25_weight=config.get("bm25_weight", 0.3),
                max_results=config.get("max_retrieval_results", 10),
                rerank_top_k=config.get("rerank_top_k", 5)
            )
            self.retriever = EnhancedRetriever(retrieval_config)
            
            # Initialize providers
            await self._initialize_providers(config)
            
            # Initialize router
            router_config = {
                "prefer_local": config.get("prefer_local", True),
                "fallback_enabled": config.get("fallback_enabled", True),
                "complexity_threshold": config.get("complexity_threshold", "moderate")
            }
            self.router = HybridRouter(router_config)
            self.router.register_providers(self.ollama_provider, self.openai_provider)
            
            self.initialized = True
            logger.info("Hybrid AI service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize hybrid AI service: {e}")
            return False
    
    async def _initialize_providers(self, config: Dict[str, Any]) -> None:
        """Initialize AI providers with graceful fallback"""
        # Initialize Ollama provider
        if config.get("enable_ollama", True):
            ollama_config = {
                "base_url": config.get("ollama_base_url", "http://localhost:11434"),
                "model": config.get("ollama_model", "mistral:7b"),
                "timeout": config.get("ollama_timeout", 30),
                "max_retries": config.get("ollama_max_retries", 2)
            }

            try:
                self.ollama_provider = OllamaProvider(ollama_config)
                logger.info(f"Ollama provider initialized: {ollama_config['base_url']} model={ollama_config['model']}")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama provider: {e} - will fallback to OpenAI if available")
        else:
            logger.info("Ollama provider disabled via config")

        # Initialize OpenAI provider
        openai_key = config.get("openai_api_key")
        if config.get("enable_openai", True) and openai_key:
            openai_config = {
                "api_key": openai_key,
                "model": config.get("openai_model", "gpt-4o-mini"),
                "timeout": config.get("openai_timeout", 30),
                "max_retries": config.get("openai_max_retries", 3)
            }

            try:
                self.openai_provider = OpenAIProvider(openai_config)
                logger.info(f"OpenAI provider initialized: model={openai_config['model']}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e} - will fallback to Ollama if available")
        else:
            if not openai_key:
                logger.info("OpenAI provider unavailable: OPENAI_API_KEY not set")
            else:
                logger.info("OpenAI provider disabled via config")

        # Warn if no providers available
        if not self.ollama_provider and not self.openai_provider:
            logger.error("No AI providers available! Check LEXA_OLLAMA_HOST and OPENAI_API_KEY environment variables")
    
    def _load_config_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        # Support both LEXA_USE_HYBRID and HYBRID_ENABLE_* variants
        use_hybrid = os.getenv("LEXA_USE_HYBRID", os.getenv("HYBRID_ENABLE_OLLAMA", "true")).lower() in ("true", "1")

        # Ollama host: support both LEXA_OLLAMA_HOST and OLLAMA_BASE_URL
        ollama_host = os.getenv("LEXA_OLLAMA_HOST", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))

        # OpenAI key with fallback
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key:
            logger.warning("OPENAI_API_KEY not set - OpenAI provider will be unavailable")

        # Hybrid threshold: support both LEXA_HYBRID_THRESHOLD and HYBRID_COMPLEXITY_THRESHOLD
        hybrid_threshold = os.getenv("LEXA_HYBRID_THRESHOLD", os.getenv("HYBRID_COMPLEXITY_THRESHOLD", "0.55"))

        # Convert threshold to complexity setting if numeric
        complexity_threshold = "moderate"
        try:
            threshold_float = float(hybrid_threshold)
            if threshold_float < 0.4:
                complexity_threshold = "simple"
            elif threshold_float > 0.7:
                complexity_threshold = "complex"
        except ValueError:
            complexity_threshold = hybrid_threshold if hybrid_threshold in ["simple", "moderate", "complex"] else "moderate"

        return {
            # Provider settings
            "enable_ollama": use_hybrid,
            "enable_openai": bool(openai_key) and os.getenv("HYBRID_ENABLE_OPENAI", "true").lower() == "true",

            # Ollama settings
            "ollama_base_url": ollama_host,
            "ollama_model": os.getenv("OLLAMA_MODEL", "mistral:7b"),
            "ollama_timeout": int(os.getenv("OLLAMA_TIMEOUT", "30")),
            "ollama_max_retries": int(os.getenv("OLLAMA_MAX_RETRIES", "2")),

            # OpenAI settings
            "openai_api_key": openai_key or None,
            "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "openai_timeout": int(os.getenv("OPENAI_TIMEOUT", "30")),
            "openai_max_retries": int(os.getenv("OPENAI_MAX_RETRIES", "3")),

            # Router settings
            "prefer_local": os.getenv("HYBRID_PREFER_LOCAL", "true").lower() == "true",
            "fallback_enabled": os.getenv("HYBRID_FALLBACK_ENABLED", "true").lower() == "true",
            "complexity_threshold": complexity_threshold,

            # Retrieval settings
            "vector_weight": float(os.getenv("HYBRID_VECTOR_WEIGHT", "0.7")),
            "bm25_weight": float(os.getenv("HYBRID_BM25_WEIGHT", "0.3")),
            "max_retrieval_results": int(os.getenv("HYBRID_MAX_RETRIEVAL_RESULTS", "10")),
            "rerank_top_k": int(os.getenv("HYBRID_RERANK_TOP_K", "5"))
        }
    
    async def generate_response(
        self, 
        query: str,
        vector_store=None,
        system_message: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate response using hybrid AI system
        """
        if not self.initialized:
            raise RuntimeError("Hybrid AI service not initialized")
        
        try:
            # 1. Enhanced retrieval
            context = ""
            retrieval_stats = {}
            
            if vector_store and self.retriever:
                search_results = await self.retriever.hybrid_search(query, vector_store)
                context = self.retriever.format_context(search_results)
                retrieval_stats = self.retriever.get_retrieval_stats(search_results)
            
            # 2. Create provider request
            request = ProviderRequest(
                prompt=query,
                context=context,
                system_message=system_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 3. Route and generate response
            response = await self.router.route_query(request)

            # 4. Return comprehensive response
            return {
                "content": response.content,
                "success": response.success,
                "provider": response.provider,
                "model": response.model,
                "latency_ms": response.latency_ms,
                "token_count": response.token_count,
                "retrieval_stats": retrieval_stats,
                "error": response.error if not response.success else None
            }
            
        except Exception as e:
            logger.error(f"Hybrid AI generation failed: {e}")
            return {
                "content": "I apologize, but I'm unable to process your request at the moment.",
                "success": False,
                "provider": "error",
                "model": "error",
                "latency_ms": 0.0,
                "token_count": 0,
                "retrieval_stats": {},
                "error": str(e)
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        if not self.initialized:
            return {"initialized": False, "error": "Service not initialized"}
        
        return {
            "initialized": True,
            "providers": self.router.get_provider_status() if self.router else {},
            "retriever_available": self.retriever is not None,
            "configuration": {
                "ollama_enabled": self.ollama_provider is not None,
                "openai_enabled": self.openai_provider is not None
            }
        }


# Global service instance
hybrid_ai_service = HybridAIService()


@asynccontextmanager
async def get_hybrid_ai_service():
    """Async context manager for hybrid AI service"""
    if not hybrid_ai_service.initialized:
        await hybrid_ai_service.initialize()
    yield hybrid_ai_service