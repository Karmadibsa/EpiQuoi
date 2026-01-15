from __future__ import annotations

import logging
import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import Settings, get_settings
from app.services.epitech_contact import scrape_campuses


logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = FastAPI(title="MCP Server", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> Dict[str, Any]:
        return {"status": "ok"}

    @app.post("/scrape/campus")
    async def scrape_campus() -> Dict[str, Any]:
        t0 = time.time()
        try:
            campuses, duration_ms = await scrape_campuses(
                timeout_sec=settings.scrape_timeout_sec,
                user_agent=settings.user_agent,
            )
        except Exception as e:
            logger.exception("Failed to scrape campuses")
            raise HTTPException(status_code=502, detail=str(e))

        return {
            "data": campuses,
            "meta": {
                "source": "epitech.eu/contact",
                "item_count": len(campuses),
                "duration_ms": duration_ms,
                "server_ms": int((time.time() - t0) * 1000),
            },
        }

    return app

