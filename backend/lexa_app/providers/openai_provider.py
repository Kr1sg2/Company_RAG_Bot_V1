"""
OpenAI Provider Implementation
Refactored from existing OpenAI integration with enhanced error handling
"""
import json
import logging
import time
from typing import Dict, Any, List, Optional

from .base_provider import BaseProvider, ProviderRequest, ProviderResponse, ProviderType

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider with comprehensive error handling"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4o-mini")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        super().__init__(config)
    
    def _get_provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    def _initialize(self) -> None:
        """Initialize OpenAI client"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            logger.info(f"Initialized OpenAI provider with model: {self.model}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def health_check(self) -> bool:
        """Check OpenAI API connectivity"""
        try:
            # Simple API test
            response = self.client.models.retrieve(self.model)
            return response.id == self.model
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "openai",
            "model": self.model,
            "base_url": self.base_url,
            "type": "cloud"
        }
    
    async def generate_response(self, request: ProviderRequest) -> ProviderResponse:
        """Generate response using OpenAI API"""
        start_time = time.time()
        
        try:
            # Build messages for chat completion
            messages = self._build_messages(request)
            
            # Make API call
            response = await self._call_openai_api(messages, request)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return self.create_response(
                content=response["content"],
                model=response["model"],
                latency_ms=latency_ms,
                success=True,
                token_count=response.get("token_count", 0)
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"OpenAI generation failed: {e}")
            
            return self.create_response(
                content="",
                model=self.model,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )
    
    def _build_messages(self, request: ProviderRequest) -> List[Dict[str, str]]:
        """Build OpenAI chat messages format"""
        messages = []
        
        # System message
        system_msg = request.system_message or self._get_default_system_message()
        messages.append({"role": "system", "content": system_msg})
        
        # Add context as user message if provided
        if request.context and request.context.strip():
            context_msg = f"Here is relevant context to help answer the question:\n\n{request.context}"
            messages.append({"role": "user", "content": context_msg})
        
        # Add the main user prompt
        messages.append({"role": "user", "content": request.prompt})
        
        return messages
    
    def _get_default_system_message(self) -> str:
        """Get default system message for company RAG"""
        return (
            "You are Lexa AI, an intelligent assistant for company employees. "
            "Your role is to help employees find information about company policies, "
            "procedures, benefits, and general workplace questions. "
            "\n\nGuidelines:\n"
            "- Use the provided context to answer questions accurately\n"
            "- If the context doesn't contain relevant information, clearly state this\n"
            "- Keep responses professional, helpful, and concise\n"
            "- Provide specific details when available in the context\n"
            "- If asked about sensitive information not in context, refer to HR or management"
        )
    
    async def _call_openai_api(self, messages: List[Dict[str, str]], request: ProviderRequest) -> Dict[str, Any]:
        """Make API call to OpenAI with retry logic"""
        import asyncio
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=request.temperature or 0.3,
                    max_tokens=request.max_tokens or 1000,
                    timeout=self.timeout
                )
                
                return {
                    "content": response.choices[0].message.content.strip(),
                    "model": response.model,
                    "token_count": response.usage.total_tokens if response.usage else 0
                }
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
                logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
        
        raise Exception("OpenAI API failed after all retry attempts")
    
    def calculate_cost(self, tokens: int) -> float:
        """Calculate approximate cost based on token usage"""
        # Rough cost estimates (as of 2024) - should be configurable
        cost_per_1k_tokens = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
            "gpt-3.5-turbo": 0.002
        }
        
        rate = cost_per_1k_tokens.get(self.model.split("-")[0], 0.002)  # Default fallback
        return (tokens / 1000) * rate