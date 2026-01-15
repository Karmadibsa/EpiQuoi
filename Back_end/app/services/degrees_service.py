"""Service for fetching degrees/programs data from MCP Server."""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class DegreesService:
    """Service for interacting with the Degrees tool exposed by MCP Server."""

    MCP_SERVER_URL = "http://localhost:8001"

    async def get_degrees_info(self) -> Optional[Dict[str, Any]]:
        """
        Trigger the degrees scraper on the MCP Server and retrieve data.

        Returns:
            Dict containing scraped degrees data or None if failed.
        """
        url = f"{self.MCP_SERVER_URL}/scrape/degrees"
        logger.info("Calling MCP Server at %s for degrees data...", url)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url)

            if response.status_code != 200:
                logger.error(
                    "MCP Server returned error for degrees: %s - %s",
                    response.status_code,
                    response.text,
                )
                return None

            data = response.json()
            print(f"🎓 [Backend] Received degrees from MCP: {data}")
            logger.info("Successfully retrieved degrees data from MCP Server.")
            return data

        except httpx.RequestError as e:
            logger.error("Failed to connect to MCP Server (degrees): %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error in DegreesService: %s", e)
            return None

