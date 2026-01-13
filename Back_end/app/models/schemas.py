"""Pydantic schemas for API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class MessageHistory(BaseModel):
    """Single message in chat history."""

    sender: str = Field(..., description="Message sender: 'user' or 'bot'")
    text: str = Field(..., description="Message content")
    isError: Optional[bool] = Field(default=False, description="Whether this is an error message")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    history: List[MessageHistory] = Field(default_factory=list, description="Chat history")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Bonjour, je suis intéressé par Epitech",
                "history": []
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="AI assistant response")
    backend_source: str = Field(..., description="Backend source information")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Bonjour ! Je suis ravi de t'aider...",
                "backend_source": "Ollama Local (llama3.1)"
            }
        }
