import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration class for the RAG scraper."""
    
    def __init__(self):
        # Output directories
        self.BASE_DIR = Path(__file__).parent
        # Use user-writable directories
        self.OUTPUT_DIR = self.BASE_DIR / "processed_files"
        self.LOG_DIR = Path.home() / ".rag_scraper_logs"
        
        # Text processing settings
        self.MAX_CHUNK_SIZE = 2000  # Maximum tokens per chunk
        self.CHUNK_OVERLAP = 100   # Token overlap between chunks
        
        # Web scraping settings
        self.REQUEST_TIMEOUT = 30   # Seconds
        self.MAX_RETRIES = 3        # Retry attempts for failed requests
        self.CONCURRENT_REQUESTS = 5  # Number of concurrent web requests
        
        # PDF processing settings
        self.PDF_MAX_PAGES = 1000   # Maximum pages to process from a PDF
        
        # Logging settings
        self.LOG_LEVEL = "INFO"
        self.LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        
    def sanitize_url_to_filename(self, url: str) -> str:
        """Sanitize URL to create a safe filename."""
        # Remove protocol
        safe_name = url.replace("http://", "").replace("https://", "")
        # Replace problematic characters (including periods)
        for char in ["/", ":", "?", "&", "=", "#", "@", "%", "+", "~", "*", "|", "\\", "<", ">", '"', "'", "`", "{", "}", "[", "]", "(", ")", ";", "!", "$", "^", "."]:
            safe_name = safe_name.replace(char, "_")
        # Remove leading/trailing underscores
        safe_name = safe_name.strip("_")
        # Add timestamp to prevent duplicates
        import time
        timestamp = int(time.time())
        safe_name = f"{safe_name}_{timestamp}"
        # Truncate if too long
        if len(safe_name) > 200:
            safe_name = safe_name[:200] + "_truncated"
        return safe_name

    def sanitize_local_filename(self, filename: str) -> str:
        """Sanitize an uploaded filename to create a safe filename."""
        # Get filename without extension
        p = Path(filename)
        safe_name = p.stem
        # Replace problematic characters
        for char in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
            safe_name = safe_name.replace(char, "_")
        # Remove leading/trailing underscores
        safe_name = safe_name.strip("_")
        # Add timestamp to prevent duplicates
        import time
        timestamp = int(time.time())
        safe_name = f"{safe_name}_{timestamp}"
        # Truncate if too long
        if len(safe_name) > 200:
            safe_name = safe_name[:200] + "_truncated"
        return safe_name

    def get_output_path(self, source: str, is_file: bool = False) -> Path:
        """Generate output file path based on URL or filename."""
        if is_file:
            safe_name = self.sanitize_local_filename(source)
        else:
            safe_name = self.sanitize_url_to_filename(source)
        return self.OUTPUT_DIR / f"{safe_name}.txt"

# Global config instance
config = Config()
