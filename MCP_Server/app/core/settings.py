from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001, ge=1, le=65535)
    log_level: str = Field(default="INFO")

    # CORS (dev-friendly default)
    cors_origins: List[str] = Field(default=["*"])

    # Scraping
    scrape_timeout_sec: int = Field(default=30, ge=5, le=300)
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

