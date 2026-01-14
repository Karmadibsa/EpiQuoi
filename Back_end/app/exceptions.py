"""Custom exceptions for the application."""

from fastapi import HTTPException, status


class ChatServiceError(HTTPException):
    """Base exception for chat service errors."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class OllamaError(ChatServiceError):
    """Exception raised when Ollama API fails."""

    def __init__(self, detail: str = "Ollama service error"):
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class NewsServiceError(ChatServiceError):
    """Exception raised when news scraping fails."""

    def __init__(self, detail: str = "News service error"):
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class GeocodingError(ChatServiceError):
    """Exception raised when geocoding fails."""

    def __init__(self, detail: str = "Geocoding service error"):
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
