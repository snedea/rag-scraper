import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from loguru import logger
from typing import List, Dict, Any
from pathlib import Path
from config import config
import os

# Ensure log directory exists
try:
    os.makedirs(config.LOG_DIR, exist_ok=True)
    # Attempt to set permissions, but don't fail if we can't
    try:
        os.chmod(config.LOG_DIR, 0o755)
    except PermissionError:
        logger.warning(f"Could not set permissions on log directory {config.LOG_DIR}")
except Exception as e:
    logger.error(f"Failed to create log directory: {str(e)}")
    raise

logger.add(config.LOG_DIR / "web_scraper.log", rotation="1 day", level=config.LOG_LEVEL)

class WebScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def init_session(self):
        """Initialize aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()

    async def fetch_url(self, url: str) -> str:
        """Fetch content from URL with retry logic."""
        try:
            for attempt in range(config.MAX_RETRIES):
                try:
                    async with self.session.get(url, timeout=config.REQUEST_TIMEOUT) as response:
                        if response.status == 200:
                            return await response.text()
                        logger.warning(f"Failed to fetch {url}, attempt {attempt + 1}/{config.MAX_RETRIES}")
                except Exception as e:
                    logger.error(f"Error fetching {url}: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            return ""
        except Exception as e:
            logger.error(f"Fatal error fetching {url}: {str(e)}")
            return ""

    def clean_html(self, html: str) -> str:
        """Clean HTML content by removing boilerplate elements."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove common boilerplate elements
        for elem in soup(['script', 'style', 'nav', 'footer', 'header']):
            elem.decompose()
            
        # Remove ads and other non-content elements
        for elem in soup.find_all(class_=lambda x: x and ('ad' in x.lower() or 'banner' in x.lower())):
            elem.decompose()
            
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        return text

    async def scrape_url(self, url: str) -> str:
        """Scrape and clean content from a URL."""
        logger.info(f"Scraping URL: {url}")
        html = await self.fetch_url(url)
        if not html:
            logger.error(f"Failed to scrape {url}")
            return ""
            
        cleaned_text = self.clean_html(html)
        logger.info(f"Successfully scraped {url}")
        return cleaned_text

    async def scrape_urls(self, urls: List[str]) -> Dict[str, str]:
        """Scrape multiple URLs concurrently."""
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return dict(zip(urls, results))

async def scrape_and_save_url(url: str) -> Path | None:
    """Scrapes a single URL, saves its content, and returns the output path."""
    scraper = WebScraper()
    await scraper.init_session()
    try:
        content = await scraper.scrape_url(url)
        if content:
            output_path = config.get_output_path(url)
            # Ensure the output directory exists
            os.makedirs(output_path.parent, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"Saved content from {url} to {output_path}")
            return output_path
        else:
            logger.error(f"No content scraped from {url}, not saving file.")
            return None
    except Exception as e:
        logger.critical(f"An unexpected error occurred while processing {url}: {e}")
        return None
    finally:
        await scraper.close_session()

async def main():
    """Example usage of WebScraper for standalone execution."""
    urls = [
        "https://www.debian.org",
        "https://en.wikipedia.org/wiki/Debian"
    ]
    tasks = [scrape_and_save_url(url) for url in urls]
    results = await asyncio.gather(*tasks)
    for url, success in zip(urls, results):
        if success:
            logger.info(f"Successfully processed {url}")
        else:
            logger.error(f"Failed to process {url}")

if __name__ == "__main__":
    asyncio.run(main())
