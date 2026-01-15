from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from .config import Settings
from .schemas import ScrapeCampusResponse, ScrapeMeta
from .scrapy_runner import ScrapyRunError, ScrapyRunner

logger = logging.getLogger(__name__)


def build_router(settings: Settings) -> APIRouter:
    router = APIRouter()
    runner = ScrapyRunner(project_dir=settings.scrapy_project_dir, timeout_sec=settings.scrape_timeout_sec)

    @router.get("/healthz")
    async def healthz() -> Dict[str, Any]:
        return {"status": "ok"}

    @router.post("/scrape/campus", response_model=ScrapeCampusResponse)
    async def scrape_campus() -> ScrapeCampusResponse:
        try:
            items, stderr, duration_ms = await runner.run_spider_json("campus_spider")
        except ScrapyRunError as e:
            logger.error("Campus spider failed: %s", e)
            raise HTTPException(status_code=502, detail=str(e))

        return ScrapeCampusResponse(
            data=items,
            meta=ScrapeMeta(
                spider="campus_spider",
                item_count=len(items),
                duration_ms=duration_ms,
                stderr_tail=(stderr[-500:] if stderr else None),
            ),
        )

    return router

