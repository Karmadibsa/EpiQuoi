from __future__ import annotations

import logging
import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import Settings, get_settings
from app.services.epitech_contact import scrape_campuses
from app.services.epitech_degrees import scrape_degrees
from app.services.epitech_pedagogy import scrape_pedagogy
from app.services.epitech_values import scrape_values


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
    async def healthz() -> Dict[str, str]:
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

    # GET alias (idempotent + nice to test in a browser/curl)
    @app.get("/scrape/campus")
    async def scrape_campus_get() -> Dict[str, Any]:
        return await scrape_campus()

    @app.post("/scrape/degrees")
    async def scrape_degrees_endpoint() -> Dict[str, Any]:
        t0 = time.time()
        try:
            degrees, duration_ms = await scrape_degrees(
                timeout_sec=settings.scrape_timeout_sec,
                user_agent=settings.user_agent,
            )
        except Exception as e:
            logger.exception("Failed to scrape degrees")
            raise HTTPException(status_code=502, detail=str(e))

        return {
            "data": degrees,
            "meta": {
                "source": "epitech.eu (official catalogue urls)",
                "item_count": len(degrees),
                "duration_ms": duration_ms,
                "server_ms": int((time.time() - t0) * 1000),
            },
        }

    # GET alias
    @app.get("/scrape/degrees")
    async def scrape_degrees_get() -> Dict[str, Any]:
        return await scrape_degrees_endpoint()

    @app.post("/scrape/pedagogy")
    async def scrape_pedagogy_endpoint() -> Dict[str, Any]:
        t0 = time.time()
        try:
            pedagogy, duration_ms = await scrape_pedagogy(
                timeout_sec=settings.scrape_timeout_sec,
                user_agent=settings.user_agent,
            )
        except Exception as e:
            logger.exception("Failed to scrape pedagogy")
            raise HTTPException(status_code=502, detail=str(e))

        return {
            "data": pedagogy,
            "meta": {
                "source": "epitech.eu/ecole-informatique-apres-bac/pedagogie",
                "duration_ms": duration_ms,
                "server_ms": int((time.time() - t0) * 1000),
            },
        }

    @app.get("/scrape/pedagogy")
    async def scrape_pedagogy_get() -> Dict[str, Any]:
        return await scrape_pedagogy_endpoint()

    @app.post("/scrape/values")
    async def scrape_values_endpoint() -> Dict[str, Any]:
        t0 = time.time()
        try:
            values, duration_ms = await scrape_values(
                timeout_sec=settings.scrape_timeout_sec,
                user_agent=settings.user_agent,
            )
        except Exception as e:
            logger.exception("Failed to scrape values")
            raise HTTPException(status_code=502, detail=str(e))

        return {
            "data": values,
            "meta": {
                "source": "epitech.eu/ecole-informatique-apres-bac/engagements",
                "duration_ms": duration_ms,
                "server_ms": int((time.time() - t0) * 1000),
            },
        }

    @app.get("/scrape/values")
    async def scrape_values_get() -> Dict[str, Any]:
        return await scrape_values_endpoint()

    return app

