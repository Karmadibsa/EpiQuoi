"""Configuration management for the application."""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    api_title: str = "EpiChat Backend"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Ollama Configuration
    ollama_model: str = Field(
        default="llama3.2:1b",  # Modèle plus léger pour éviter le blocage
        description="Ollama model name (recommandé: llama3.2:1b ou llama3.2:3b pour Mac)"
    )
    ollama_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_timeout: int = Field(
        default=120,  # 2 minutes max pour éviter le blocage
        ge=10,
        le=600,
        description="Timeout for Ollama requests in seconds"
    )

    # Scraper Configuration
    scraper_path: str = Field(
        default="../MCP_Server/epitech_scraper",
        description="Path to the Scrapy scraper"
    )
    max_news_items: int = Field(default=3, ge=1, le=10)

    # Geocoding Configuration
    geocoding_timeout: int = Field(default=10, ge=1, le=60)

    # Language Detection
    min_words_for_lang_detection: int = Field(default=8, ge=1)

    # History Configuration
    max_history_messages: int = Field(default=10, ge=1, le=50)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env instead of raising error

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


# Global settings instance
settings = Settings()
