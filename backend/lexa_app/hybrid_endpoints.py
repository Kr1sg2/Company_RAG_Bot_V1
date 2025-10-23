"""
FastAPI endpoints for Hybrid AI functionality
Integrates with existing Lexa AI API structure
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from .hybrid_ai import get_hybrid_ai_service

logger = logging.getLogger(__name__)

# Create router for hybrid AI endpoints
hybrid_router = APIRouter(prefix="/hybrid", tags=["Hybrid AI"])


class HybridChatRequest(BaseModel):
    """Request model for hybrid chat"""
    query: str = Field(..., description="User query")
    system_message: Optional[str] = Field(None, description="Custom system message")
    temperature: Optional[float] = Field(0.3, ge=0.0, le=2.0, description="Response creativity")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Maximum response tokens")
    use_retrieval: Optional[bool] = Field(True, description="Enable enhanced retrieval")


class HybridChatResponse(BaseModel):
    """Response model for hybrid chat"""
    content: str = Field(..., description="AI response content")
    success: bool = Field(..., description="Whether the request succeeded")
    provider: str = Field(..., description="Provider used (ollama/openai)")
    model: str = Field(..., description="Model used for generation")
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    token_count: int = Field(..., description="Token count estimate")
    retrieval_stats: Dict[str, Any] = Field({}, description="Retrieval statistics")
    error: Optional[str] = Field(None, description="Error message if failed")


class ServiceStatusResponse(BaseModel):
    """Response model for service status"""
    initialized: bool = Field(..., description="Service initialization status")
    providers: Dict[str, Any] = Field({}, description="Provider availability and health")
    retriever_available: bool = Field(..., description="Enhanced retrieval availability")
    configuration: Dict[str, Any] = Field({}, description="Service configuration")


@hybrid_router.post("/chat", response_model=HybridChatResponse)
async def hybrid_chat(
    request: HybridChatRequest,
    vector_store_collection=None  # This would be injected by the existing app
):
    """
    Generate response using hybrid AI system
    Routes between Ollama (local) and OpenAI (cloud) based on query complexity
    """
    try:
        async with get_hybrid_ai_service() as hybrid_service:
            # Use retrieval only if requested and vector store available
            store = vector_store_collection if request.use_retrieval else None
            
            response = await hybrid_service.generate_response(
                query=request.query,
                vector_store=store,
                system_message=request.system_message,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            return HybridChatResponse(**response)
    
    except Exception as e:
        logger.error(f"Hybrid chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid chat failed: {str(e)}")


@hybrid_router.get("/status", response_model=ServiceStatusResponse)
async def get_hybrid_status():
    """
    Get hybrid AI service status and configuration
    """
    try:
        async with get_hybrid_ai_service() as hybrid_service:
            status = hybrid_service.get_service_status()
            return ServiceStatusResponse(**status)
    
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@hybrid_router.post("/initialize")
async def initialize_hybrid_service(background_tasks: BackgroundTasks):
    """
    Manually initialize/reinitialize the hybrid service
    """
    try:
        async with get_hybrid_ai_service() as hybrid_service:
            success = await hybrid_service.initialize()
            
            if success:
                return {"message": "Hybrid AI service initialized successfully", "success": True}
            else:
                raise HTTPException(status_code=500, detail="Failed to initialize hybrid service")
    
    except Exception as e:
        logger.error(f"Initialize endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@hybrid_router.get("/providers")
async def get_provider_info():
    """
    Get detailed information about available providers
    """
    try:
        async with get_hybrid_ai_service() as hybrid_service:
            if not hybrid_service.initialized:
                raise HTTPException(status_code=503, detail="Service not initialized")
            
            provider_info = {}
            
            # Get Ollama info
            if hybrid_service.ollama_provider:
                provider_info["ollama"] = {
                    "available": True,
                    "healthy": hybrid_service.ollama_provider.health_check(),
                    "model_info": hybrid_service.ollama_provider.get_model_info()
                }
            else:
                provider_info["ollama"] = {"available": False}
            
            # Get OpenAI info  
            if hybrid_service.openai_provider:
                provider_info["openai"] = {
                    "available": True,
                    "healthy": hybrid_service.openai_provider.health_check(),
                    "model_info": hybrid_service.openai_provider.get_model_info()
                }
            else:
                provider_info["openai"] = {"available": False}
            
            return provider_info
    
    except Exception as e:
        logger.error(f"Provider info endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Provider info failed: {str(e)}")


# Health check endpoint
@hybrid_router.get("/health")
async def health_check():
    """
    Simple health check for hybrid AI system
    """
    try:
        async with get_hybrid_ai_service() as hybrid_service:
            return {
                "status": "healthy",
                "initialized": hybrid_service.initialized,
                "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
            }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e),
            "initialized": False
        }


# Legacy compatibility endpoint
@hybrid_router.post("/legacy/chat")
async def legacy_chat_compatibility(
    query: str,
    system_message: Optional[str] = None,
    vector_store_collection=None
):
    """
    Legacy compatibility endpoint that matches existing chat API
    Allows gradual migration to hybrid system
    """
    try:
        request = HybridChatRequest(
            query=query,
            system_message=system_message,
            temperature=0.3,
            max_tokens=1000,
            use_retrieval=True
        )
        
        response = await hybrid_chat(request, vector_store_collection)
        
        # Return in legacy format
        return {
            "response": response.content,
            "success": response.success,
            "metadata": {
                "provider": response.provider,
                "model": response.model,
                "latency_ms": response.latency_ms,
                "token_count": response.token_count
            }
        }
    
    except Exception as e:
        logger.error(f"Legacy chat error: {e}")
        return {
            "response": "I apologize, but I'm unable to process your request at the moment.",
            "success": False,
            "error": str(e)
        }