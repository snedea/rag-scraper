import io
import logging
from loguru import logger
from typing import List, Dict, Any
from config import config
import pdfminer
from pdfminer.high_level import extract_text
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

logger.add(config.LOG_DIR / "pdf_scraper.log", rotation="1 day", level=config.LOG_LEVEL)

class PDFScraper:
    def __init__(self):
        pass

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            text = extract_text(pdf_path)
            logger.info(f"Successfully extracted text from {pdf_path}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""

    def clean_pdf_text(self, text: str) -> str:
        """Clean extracted PDF text by removing common artifacts."""
        # Remove page numbers (simple heuristic)
        cleaned = text.replace("\n\n", "\n")  # Remove double newlines
        cleaned = "\n".join(line for line in cleaned.split("\n") if line.strip())
        return cleaned

    def process_pdf(self, pdf_path: str) -> str:
        """Process a PDF file and return cleaned text."""
        logger.info(f"Processing PDF: {pdf_path}")
        text = self.extract_text(pdf_path)
        if not text:
            logger.error(f"Failed to process PDF: {pdf_path}")
            return ""
            
        cleaned_text = self.clean_pdf_text(text)
        logger.info(f"Successfully processed PDF: {pdf_path}")
        return cleaned_text

    def process_pdfs(self, pdf_paths: List[str]) -> Dict[str, str]:
        """Process multiple PDF files."""
        results = {}
        for pdf_path in pdf_paths:
            text = self.process_pdf(pdf_path)
            results[pdf_path] = text
        return results

async def main():
    """Example usage of PDFScraper."""
    scraper = PDFScraper()
    
    pdf_paths = [
        "path/to/document1.pdf",
        "path/to/document2.pdf"
    ]
    
    results = scraper.process_pdfs(pdf_paths)
    for pdf_path, content in results.items():
        if content:
            output_path = config.get_output_path(pdf_path)
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"Saved content to {output_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
