"""Chat endpoint routes."""

import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.exceptions import ChatServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize service
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return AI response.
    
    Args:
        request: Chat request with message and history
    
    Returns:
        Chat response with AI message and backend source
    
    Raises:
        HTTPException: If chat processing fails
    """
    try:
        result = await chat_service.process_chat(request)
        return ChatResponse(**result)
    except ChatServiceError as e:
        logger.error(f"Chat service error: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
