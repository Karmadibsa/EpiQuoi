"""Service for fetching Epitech news."""

import asyncio
import json
import os
import logging
from typing import List, Dict

from app.config import settings
from app.exceptions import NewsServiceError

logger = logging.getLogger(__name__)


class NewsService:
    """Service for scraping Epitech news."""

    @staticmethod
    async def get_epitech_news() -> str:
        """
        Fetch latest Epitech news using Scrapy scraper.
        
        Returns:
            Formatted news string
        
        Raises:
            NewsServiceError: If scraping fails
        """
        try:
            import time
            start_time = time.time()
            
            scraper_path = os.path.join(
                os.path.dirname(__file__),
                "../../..",
                settings.scraper_path.lstrip("../")
            )
            scraper_path = os.path.abspath(scraper_path)
            
            print(f"   📡 Chemin scraper: {scraper_path}")
            logger.info(f"Running Scrapy scraper from: {scraper_path}")
            
            # Run Scrapy asynchronously
            print("   ⏳ Lancement de Scrapy...")
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "scrapy", "crawl", "epitech_news", "-O", "-", "-t", "json",
                cwd=scraper_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            elapsed_time = time.time() - start_time
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                print(f"   ❌ Erreur Scrapy après {elapsed_time:.2f}s: {error_msg[:100]}")
                logger.error(f"Scrapy error: {error_msg}")
                raise NewsServiceError(f"Failed to fetch news: {error_msg}")
            
            # Parse JSON from stdout
            news_data = json.loads(stdout.decode())
            
            if not news_data:
                print(f"   ⚠️  Aucune actualité trouvée après {elapsed_time:.2f}s")
                return "Aucune actualité disponible pour le moment."
            
            # Format news items
            formatted_news = "Voici les dernières actualités Epitech récupérées en direct :\n"
            items_count = min(len(news_data), settings.max_news_items)
            for item in news_data[:settings.max_news_items]:
                title = item.get('title', 'Sans titre').strip()
                summary = item.get('summary', '').strip()
                link = item.get('link', '#')
                formatted_news += f"- {title}: {summary} (Source: {link})\n"
            
            print(f"   ✓ {items_count} actualités récupérées en {elapsed_time:.2f}s")
            
            return formatted_news
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse news JSON: {e}")
            raise NewsServiceError("Failed to parse news data")
        except Exception as e:
            logger.error(f"Unexpected error fetching news: {e}")
            raise NewsServiceError(f"Unexpected error: {str(e)}")
