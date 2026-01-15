"""Chat endpoint routes."""

import logging
import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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


@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest) -> StreamingResponse:
    """
    SSE stream endpoint returning progress events + final response.
    """

    queue: asyncio.Queue[dict] = asyncio.Queue()

    async def progress_cb(phase: str, payload: dict) -> None:
        await queue.put({"type": "progress", "phase": phase, **payload})

    async def run_chat() -> None:
        try:
            result = await chat_service.process_chat(request, progress_cb=progress_cb)
            await queue.put({"type": "final", **result})
        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})
        finally:
            await queue.put({"type": "done"})

    async def event_generator():
        task = asyncio.create_task(run_chat())
        try:
            while True:
                item = await queue.get()
                t = item.get("type")
                if t == "done":
                    break
                yield "event: message\n"
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        finally:
            task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
