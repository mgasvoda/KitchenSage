"""
Chat API endpoint with SSE streaming support.
"""

import json
import asyncio
from typing import Optional, List, AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.services import ChatService

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None, 
        description="Previous conversation messages for context"
    )


class ChatResponse(BaseModel):
    """Chat response model for non-streaming responses."""
    message: str
    intent: Optional[str] = None
    status: str = "success"


async def generate_sse_stream(message: str, history: Optional[List[ChatMessage]]) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events stream for chat response.
    
    Yields SSE-formatted messages as the AI processes the request.
    """
    service = ChatService()
    
    # Convert history to the format expected by the service
    history_dicts = None
    if history:
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in history]
    
    try:
        # Send initial event to indicate processing started
        yield f"data: {json.dumps({'type': 'start', 'content': ''})}\n\n"
        
        # Process the message using the chat service
        async for chunk in service.process_message_stream(message, history_dicts):
            if chunk.get("type") == "token":
                # Stream individual tokens
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.get('content', '')})}\n\n"
            elif chunk.get("type") == "thinking":
                # Stream thinking/processing status
                yield f"data: {json.dumps({'type': 'thinking', 'content': chunk.get('content', '')})}\n\n"
            elif chunk.get("type") == "complete":
                # Final complete message
                yield f"data: {json.dumps({'type': 'complete', 'content': chunk.get('content', ''), 'intent': chunk.get('intent')})}\n\n"
            elif chunk.get("type") == "error":
                yield f"data: {json.dumps({'type': 'error', 'content': chunk.get('content', 'An error occurred')})}\n\n"
        
        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("", response_class=StreamingResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint with Server-Sent Events streaming.
    
    Sends a message to the AI assistant and streams back the response
    in real-time using SSE format.
    
    Event types:
    - start: Processing has begun
    - thinking: AI is processing (status update)
    - token: Individual response token
    - complete: Full response is ready
    - error: An error occurred
    - done: Stream is complete
    """
    return StreamingResponse(
        generate_sse_stream(request.message, request.conversation_history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest):
    """
    Synchronous chat endpoint (non-streaming).
    
    Useful for simpler integrations that don't need streaming.
    """
    service = ChatService()
    
    # Convert history to the format expected by the service
    history_dicts = None
    if request.conversation_history:
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
    
    result = await service.process_message(request.message, history_dicts)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Chat processing failed"))
    
    return ChatResponse(
        message=result.get("response", ""),
        intent=result.get("intent"),
        status="success"
    )

