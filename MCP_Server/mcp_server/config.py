from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001, ge=1, le=65535)
    log_level: str = Field(default="INFO")

    # CORS (dev-friendly by default)
    cors_origins: List[str] = Field(default=["*"])

    # Scrapy
    scrape_timeout_sec: int = Field(default=90, ge=5, le=600)

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False

    @property
    def scrapy_project_dir(self) -> Path:
        # .../MCP_Server/mcp_server/config.py -> .../MCP_Server
        root = Path(__file__).resolve().parents[1]
        return root / "epitech_scraper"


@lru_cache
def get_settings() -> Settings:
    return Settings()

