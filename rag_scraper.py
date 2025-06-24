import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
from config import config
from web_scraper import WebScraper
from pdf_scraper import PDFScraper
import os

# Ensure log directory exists with proper permissions
os.makedirs(config.LOG_DIR, exist_ok=True)
os.chmod(config.LOG_DIR, 0o755)

logger.add(config.LOG_DIR / "rag_scraper.log", rotation="1 day", level=config.LOG_LEVEL)

class RAGScraper:
    def __init__(self):
        self.web_scraper = WebScraper()
        self.pdf_scraper = PDFScraper()
        self.output_dir = config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def scrape_web_content(self, urls: List[str]) -> Dict[str, str]:
        """Scrape and save web content."""
        logger.info(f"Scraping {len(urls)} web URLs")
        await self.web_scraper.init_session()
        try:
            results = await self.web_scraper.scrape_urls(urls)
            for url, content in results.items():
                if content:
                    output_path = config.get_output_path(url)
                    output_path.write_text(content, encoding='utf-8')
                    logger.info(f"Saved content from {url} to {output_path}")
            return results
        finally:
            await self.web_scraper.close_session()

    def scrape_pdf_content(self, pdf_paths: List[str]) -> Dict[str, str]:
        """Scrape and save PDF content."""
        logger.info(f"Processing {len(pdf_paths)} PDF files")
        results = self.pdf_scraper.process_pdfs(pdf_paths)
        for pdf_path, content in results.items():
            if content:
                output_path = config.get_output_path(pdf_path)
                output_path.write_text(content, encoding='utf-8')
                logger.info(f"Saved content from {pdf_path} to {output_path}")
        return results

    async def process_content(self, urls: List[str], pdf_paths: List[str]):
        """Process both web and PDF content."""
        web_results = await self.scrape_web_content(urls)
        pdf_results = self.scrape_pdf_content(pdf_paths)
        return web_results, pdf_results

async def main():
    """Main entry point for the RAG scraper."""
    parser = argparse.ArgumentParser(description='RAG Scraper for web pages and PDFs')
    parser.add_argument('--urls', nargs='+', help='List of URLs to scrape')
    parser.add_argument('--pdfs', nargs='+', help='List of PDF files to process')
    parser.add_argument('--output-dir', default=config.OUTPUT_DIR, help='Output directory for processed content')
    parser.add_argument('--log-level', default=config.LOG_LEVEL, help='Logging level (DEBUG, INFO, WARNING, ERROR)')

    args = parser.parse_args()
    
    # Set log level
    logger.remove()
    logger.add(config.LOG_DIR / "rag_scraper.log", rotation="1 day", level=args.log_level)

    scraper = RAGScraper()
    
    try:
        web_results, pdf_results = await scraper.process_content(
            args.urls or [],
            args.pdfs or []
        )
        
        logger.info("Scraping completed successfully")
        logger.info(f"Processed {len(web_results)} web URLs and {len(pdf_results)} PDF files")
        
        print("\nSummary:")
        print(f"Processed URLs: {len(web_results)}")
        print(f"Processed PDFs: {len(pdf_results)}")
        print(f"Output directory: {args.output_dir}")
        print("\nFiles have been saved to the output directory and are ready for Open WebUI ingestion.")
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
