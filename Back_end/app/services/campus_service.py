"""Service for fetching campus data from MCP Server."""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CampusService:
    """Service for interacting with the Campus Scraper via MCP Server."""
    
    MCP_SERVER_URL = "http://localhost:8001"

    async def get_campus_info(self) -> Optional[Dict[str, Any]]:
        """
        Trigger the campus spider on the MCP Server and retrieve data.
        
        Returns:
            Dict containing scraped campus data or None if failed.
        """
        url = f"{self.MCP_SERVER_URL}/scrape/campus"
        logger.info(f"Calling MCP Server at {url} for campus data...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url)
                
                if response.status_code != 200:
                    logger.error(f"MCP Server returned error: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                print(f"📦 [Backend] Received from MCP: {data}")
                logger.info("Successfully retrieved campus data from MCP Server.")
                return data

        except httpx.RequestError as e:
            logger.error(f"Failed to connect to MCP Server: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in CampusService: {e}")
            return None
