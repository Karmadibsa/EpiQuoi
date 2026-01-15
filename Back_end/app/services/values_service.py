"""Service for fetching Epitech values/devise info from MCP Server."""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ValuesService:
    MCP_SERVER_URL = "http://localhost:8001"

    async def get_values_info(self) -> Optional[Dict[str, Any]]:
        url = f"{self.MCP_SERVER_URL}/scrape/values"
        logger.info("Calling MCP Server at %s for values data...", url)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url)

            if response.status_code != 200:
                logger.error(
                    "MCP Server returned error for values: %s - %s",
                    response.status_code,
                    response.text,
                )
                return None

            data = response.json()
            return data
        except httpx.RequestError as e:
            logger.error("Failed to connect to MCP Server (values): %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error in ValuesService: %s", e)
            return None

