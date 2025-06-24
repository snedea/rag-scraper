from pathlib import Path
from pdfminer.high_level import extract_text
from loguru import logger
from config import config
import os

def process_pdf(file_path: Path, original_filename: str) -> Path | None:
    """Extracts text from a PDF file and saves it to the output directory."""
    logger.info(f"Processing PDF: {original_filename}")
    try:
        # Extract text from the PDF
        text = extract_text(str(file_path))

        if not text.strip():
            logger.warning(f"No text could be extracted from {original_filename}.")
            return None

        # Generate a safe output path
        output_path = config.get_output_path(original_filename, is_file=True)
        
        # Ensure the output directory exists
        os.makedirs(output_path.parent, exist_ok=True)

        # Save the extracted text
        output_path.write_text(text, encoding='utf-8')
        logger.info(f"Successfully processed and saved {original_filename} to {output_path}")
        return output_path
    except Exception as e:
        logger.critical(f"An error occurred while processing {original_filename}: {e}")
        return None
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed temporary file: {file_path}")
