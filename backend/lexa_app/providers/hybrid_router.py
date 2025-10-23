"""
Hybrid Router - Intelligent routing between Ollama and OpenAI providers
Routes queries based on complexity, performance requirements, and availability
"""
import logging
import re
from typing import Dict, Any, Optional, List
from enum import Enum

from .base_provider import BaseProvider, ProviderRequest, ProviderResponse, ProviderType

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels for routing decisions"""
    SIMPLE = "simple"          # Basic lookups, simple Q&A
    MODERATE = "moderate"      # Analysis, comparisons
    COMPLEX = "complex"        # Multi-step reasoning, creative tasks


class HybridRouter:
    """
    Intelligent router that selects the best provider for each query
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ollama_provider: Optional[BaseProvider] = None
        self.openai_provider: Optional[BaseProvider] = None
        
        # Routing preferences
        self.prefer_local = config.get("prefer_local", True)
        self.fallback_enabled = config.get("fallback_enabled", True)
        self.complexity_threshold = config.get("complexity_threshold", "moderate")
        
        # Performance tracking
        self.provider_performance = {
            ProviderType.OLLAMA: {"success_rate": 1.0, "avg_latency": 0.0},
            ProviderType.OPENAI: {"success_rate": 1.0, "avg_latency": 0.0}
        }
    
    def register_providers(self, ollama: BaseProvider, openai: BaseProvider) -> None:
        """Register available providers"""
        self.ollama_provider = ollama
        self.openai_provider = openai
        logger.info("Registered Ollama and OpenAI providers with hybrid router")
    
    async def route_query(self, request: ProviderRequest) -> ProviderResponse:
        """
        Route query to best available provider
        """
        # 1. Analyze query complexity
        complexity = self._analyze_complexity(request.prompt)

        # 2. Select primary provider
        primary_provider, selection_reason = self._select_provider(complexity, request)

        # 3. Attempt with primary provider
        if primary_provider:
            provider_name = primary_provider.get_provider_type().value
            logger.info(f"router=hybrid provider={provider_name} reason={selection_reason}")

            response = await primary_provider.generate_response(request)

            # Update performance metrics
            self._update_performance_metrics(primary_provider.get_provider_type(), response)

            if response.success:
                logger.info(f"router=hybrid provider={provider_name} status=success latency_ms={response.latency_ms:.1f}")
                return response
            else:
                logger.warning(f"router=hybrid provider={provider_name} status=failed error={response.error}")

        # 4. Fallback if enabled and primary failed
        if self.fallback_enabled:
            fallback_provider = self._get_fallback_provider(primary_provider)
            if fallback_provider:
                fallback_name = fallback_provider.get_provider_type().value
                logger.warning(f"router=hybrid provider={fallback_name} reason=fallback_from_{primary_provider.get_provider_type().value if primary_provider else 'none'}")
                response = await fallback_provider.generate_response(request)
                self._update_performance_metrics(fallback_provider.get_provider_type(), response)

                if response.success:
                    logger.info(f"router=hybrid provider={fallback_name} status=success_after_fallback")
                return response

        # 5. Return failure response if all providers failed
        logger.error("router=hybrid provider=none reason=all_providers_unavailable")
        return ProviderResponse(
            content="I'm currently unable to process your request. Please try again later.",
            provider_type=ProviderType.OPENAI,  # Default for error
            model="error",
            latency_ms=0.0,
            success=False,
            error="All providers unavailable"
        )
    
    def _analyze_complexity(self, prompt: str) -> QueryComplexity:
        """
        Analyze query complexity using heuristics
        """
        prompt_lower = prompt.lower()
        
        # Complex indicators
        complex_patterns = [
            r'\b(analyze|compare|evaluate|explain why|reasoning|because)\b',
            r'\b(step by step|procedure|process|workflow)\b',
            r'\b(calculate|compute|determine|solve)\b',
            r'\b(write|create|generate|compose|draft)\b',
            r'\b(multiple|several|various|different)\b.*\b(options|approaches|methods)\b',
        ]
        
        # Simple indicators
        simple_patterns = [
            r'^\s*(what is|who is|when is|where is|how much|how many)\b',
            r'^\s*(define|definition of)\b',
            r'^\s*(list|show me|find|lookup)\b',
            r'^\s*(yes or no|true or false)\b',
        ]
        
        # Check for complex patterns
        for pattern in complex_patterns:
            if re.search(pattern, prompt_lower):
                return QueryComplexity.COMPLEX
        
        # Check for simple patterns
        for pattern in simple_patterns:
            if re.search(pattern, prompt_lower):
                return QueryComplexity.SIMPLE
        
        # Check length and structure
        if len(prompt.split()) > 50:  # Long queries often complex
            return QueryComplexity.COMPLEX
        elif len(prompt.split()) < 10:  # Short queries often simple
            return QueryComplexity.SIMPLE
        
        return QueryComplexity.MODERATE
    
    def _select_provider(self, complexity: QueryComplexity, request: ProviderRequest) -> tuple[Optional[BaseProvider], str]:
        """
        Select the best provider based on complexity and availability
        Returns (provider, reason) tuple
        """
        # Check availability first
        ollama_healthy = self.ollama_provider and self.ollama_provider.health_check()
        openai_healthy = self.openai_provider and self.openai_provider.health_check()

        if not ollama_healthy and not openai_healthy:
            logger.error("No healthy providers available")
            return None, "no_healthy_providers"

        # Simple routing logic
        if complexity == QueryComplexity.SIMPLE and ollama_healthy and self.prefer_local:
            return self.ollama_provider, f"simple_query_prefer_local"

        if complexity == QueryComplexity.COMPLEX and openai_healthy:
            return self.openai_provider, f"complex_query_needs_advanced_reasoning"

        # Moderate complexity - use performance metrics
        if complexity == QueryComplexity.MODERATE:
            if self.prefer_local and ollama_healthy:
                ollama_perf = self.provider_performance[ProviderType.OLLAMA]
                if ollama_perf["success_rate"] > 0.8:  # Good success rate
                    return self.ollama_provider, f"moderate_query_good_local_perf"

        # Default fallback
        if openai_healthy:
            return self.openai_provider, f"default_fallback_to_cloud"
        elif ollama_healthy:
            return self.ollama_provider, f"default_fallback_to_local"

        return None, "no_provider_selected"
    
    def _get_fallback_provider(self, primary: Optional[BaseProvider]) -> Optional[BaseProvider]:
        """Get fallback provider (opposite of primary)"""
        if not primary:
            return None
        
        if primary.get_provider_type() == ProviderType.OLLAMA:
            return self.openai_provider if self.openai_provider and self.openai_provider.health_check() else None
        else:
            return self.ollama_provider if self.ollama_provider and self.ollama_provider.health_check() else None
    
    def _update_performance_metrics(self, provider_type: ProviderType, response: ProviderResponse) -> None:
        """Update provider performance tracking"""
        if provider_type not in self.provider_performance:
            return
        
        metrics = self.provider_performance[provider_type]
        
        # Update success rate (rolling average)
        current_success = 1.0 if response.success else 0.0
        metrics["success_rate"] = (metrics["success_rate"] * 0.9) + (current_success * 0.1)
        
        # Update average latency
        if response.latency_ms > 0:
            metrics["avg_latency"] = (metrics["avg_latency"] * 0.9) + (response.latency_ms * 0.1)
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get current status of all providers"""
        return {
            "ollama": {
                "available": self.ollama_provider is not None,
                "healthy": self.ollama_provider.health_check() if self.ollama_provider else False,
                "performance": self.provider_performance.get(ProviderType.OLLAMA, {})
            },
            "openai": {
                "available": self.openai_provider is not None,
                "healthy": self.openai_provider.health_check() if self.openai_provider else False,
                "performance": self.provider_performance.get(ProviderType.OPENAI, {})
            },
            "routing_config": {
                "prefer_local": self.prefer_local,
                "fallback_enabled": self.fallback_enabled,
                "complexity_threshold": self.complexity_threshold
            }
        }