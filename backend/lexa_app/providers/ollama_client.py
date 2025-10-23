"""
Ollama Provider Implementation
Integrates with local Ollama instance for fast, private AI responses
"""
import json
import logging
import time
import aiohttp
import asyncio
from typing import Dict, Any, Optional

from .base_provider import BaseProvider, ProviderRequest, ProviderResponse, ProviderType

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "mistral:7b")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 2)
        super().__init__(config)
    
    def _get_provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA
    
    def _initialize(self) -> None:
        """Initialize Ollama connection"""
        logger.info(f"Initializing Ollama provider: {self.base_url}, model: {self.model}")
    
    def health_check(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            import requests
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if model is available
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            return any(self.model in name for name in model_names)
            
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "type": "local"
        }
    
    async def generate_response(self, request: ProviderRequest) -> ProviderResponse:
        """Generate response using Ollama"""
        start_time = time.time()
        
        try:
            # Prepare the prompt
            full_prompt = self._build_prompt(request)
            
            # Make request to Ollama
            response_content = await self._call_ollama_api(full_prompt, request)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return self.create_response(
                content=response_content,
                model=self.model,
                latency_ms=latency_ms,
                success=True,
                token_count=self.estimate_tokens(response_content)
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Ollama generation failed: {e}")
            
            return self.create_response(
                content="",
                model=self.model,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )
    
    def _build_prompt(self, request: ProviderRequest) -> str:
        """Build the complete prompt for Ollama"""
        system_msg = request.system_message or self._get_default_system_message()
        
        prompt_parts = []
        
        # Add system message
        if system_msg:
            prompt_parts.append(f"System: {system_msg}")
        
        # Add context if provided
        if request.context and request.context.strip():
            prompt_parts.append(f"Context:\n{request.context}")
        
        # Add the main prompt
        prompt_parts.append(f"Human: {request.prompt}")
        prompt_parts.append("Assistant: ")
        
        return "\n\n".join(prompt_parts)
    
    def _get_default_system_message(self) -> str:
        """Get default system message for company RAG"""
        return (
            "You are Lexa AI, a helpful assistant for company employees. "
            "Use the provided context to answer questions about company policies, "
            "procedures, and information. If the context doesn't contain relevant "
            "information, say so clearly. Keep responses concise and helpful."
        )
    
    async def _call_ollama_api(self, prompt: str, request: ProviderRequest) -> str:
        """Make API call to Ollama"""
        # Limit tokens for CPU performance - Ollama on CPU is slower
        # Cap at 512 tokens regardless of request to prevent timeouts
        max_tokens = min(request.max_tokens or 512, 512) if request.max_tokens else 512

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,  # Get complete response
            "options": {
                "temperature": request.temperature or 0.3,
                "num_predict": max_tokens
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                
                if "error" in result:
                    raise Exception(f"Ollama error: {result['error']}")
                
                return result.get("response", "").strip()
    
    def pull_model_if_needed(self) -> bool:
        """Pull the model if it's not available"""
        try:
            import requests
            
            logger.info(f"Pulling Ollama model: {self.model}")
            
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                stream=True,
                timeout=300  # 5 minutes for model download
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to pull model: {response.status_code}")
                return False
            
            # Stream the pull progress
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "status" in data:
                            logger.info(f"Model pull: {data['status']}")
                    except json.JSONDecodeError:
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {self.model}: {e}")
            return False