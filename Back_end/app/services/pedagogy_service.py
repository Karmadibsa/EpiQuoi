"""Service for fetching pedagogy/methodology info from MCP Server."""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class PedagogyService:
    """Service for interacting with the Pedagogy tool exposed by MCP Server."""

    MCP_SERVER_URL = "http://localhost:8001"

    async def get_pedagogy_info(self) -> Optional[Dict[str, Any]]:
        url = f"{self.MCP_SERVER_URL}/scrape/pedagogy"
        logger.info("Calling MCP Server at %s for pedagogy data...", url)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url)

            if response.status_code != 200:
                logger.error(
                    "MCP Server returned error for pedagogy: %s - %s",
                    response.status_code,
                    response.text,
                )
                return None

            data = response.json()
            print(f"📚 [Backend] Received pedagogy from MCP: {data}")
            return data
        except httpx.RequestError as e:
            logger.error("Failed to connect to MCP Server (pedagogy): %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error in PedagogyService: %s", e)
            return None

