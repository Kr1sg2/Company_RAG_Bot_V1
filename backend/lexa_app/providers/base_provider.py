"""
AI Provider Interface
Defines the base contract for all AI providers (OpenAI, Ollama, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import time


class ProviderType(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    HYBRID = "hybrid"


@dataclass
class ProviderResponse:
    """Standardized response from AI providers"""
    content: str
    provider: str
    model: str
    latency_ms: float
    token_count: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    success: bool = True


@dataclass
class ProviderRequest:
    """Standardized request to AI providers"""
    prompt: str
    context: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base class for all AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_type = self._get_provider_type()
        self._initialize()
    
    @abstractmethod
    def _get_provider_type(self) -> ProviderType:
        """Return the provider type"""
        pass
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize provider-specific configuration"""
        pass
    
    @abstractmethod
    async def generate_response(self, request: ProviderRequest) -> ProviderResponse:
        """Generate a response from the provider"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the provider is available and healthy"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        pass
    
    def get_provider_type(self) -> ProviderType:
        """Return the provider type"""
        return self.provider_type

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    def create_response(self, content: str, model: str, latency_ms: float,
                       success: bool = True, error: str = None, **kwargs) -> ProviderResponse:
        """Helper to create standardized response"""
        return ProviderResponse(
            content=content,
            provider=self.provider_type.value,
            model=model,
            latency_ms=latency_ms,
            success=success,
            error=error,
            **kwargs
        )


class ProviderManager:
    """Manages multiple AI providers"""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.fallback_order = ["ollama", "openai"]  # Default fallback order
    
    def register_provider(self, name: str, provider: BaseProvider):
        """Register a new provider"""
        self.providers[name] = provider
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name"""
        return self.providers.get(name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of healthy providers"""
        available = []
        for name, provider in self.providers.items():
            try:
                if provider.health_check():
                    available.append(name)
            except Exception:
                continue
        return available
    
    def get_fallback_provider(self, preferred: str = None) -> Optional[BaseProvider]:
        """Get the best available provider with fallback logic"""
        # Try preferred provider first
        if preferred and preferred in self.providers:
            provider = self.providers[preferred]
            try:
                if provider.health_check():
                    return provider
            except Exception:
                pass
        
        # Try fallback order
        for provider_name in self.fallback_order:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                try:
                    if provider.health_check():
                        return provider
                except Exception:
                    continue
        
        return None