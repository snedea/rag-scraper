#!/usr/bin/env python3
"""
Daily RAG ingestion script that processes new documents and adds them to OpenWebUI
"""
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger

# Configuration
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://openwebui:8080")
API_KEY = os.getenv("OPEN_WEBUI_API_KEY")
PROCESSED_FILES_DIR = Path("processed_files")
KNOWLEDGE_COLLECTION_NAME = "rag_documents"

# Track processed files to avoid duplicates
PROCESSED_TRACKER_FILE = Path("daily_ingest_tracker.txt")

def load_processed_files() -> set:
    """Load the set of already processed files"""
    if PROCESSED_TRACKER_FILE.exists():
        with open(PROCESSED_TRACKER_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_processed_file(filename: str):
    """Save a processed filename to the tracker"""
    with open(PROCESSED_TRACKER_FILE, 'a') as f:
        f.write(f"{filename}\n")

def get_new_files_since_yesterday() -> List[Path]:
    """Get files created or modified in the last 24 hours"""
    cutoff_time = time.time() - (24 * 60 * 60)  # 24 hours ago
    processed_files = load_processed_files()
    
    new_files = []
    for file_path in PROCESSED_FILES_DIR.glob("*.txt"):
        # Check if file is new or modified recently
        if (file_path.stat().st_mtime > cutoff_time and 
            file_path.name not in processed_files):
            new_files.append(file_path)
    
    return new_files

def get_or_create_knowledge_collection() -> Optional[str]:
    """Get existing knowledge collection or create new one"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Check if collection exists
    try:
        response = requests.get(f"{OPEN_WEBUI_URL}/api/v1/knowledge/", headers=headers)
        response.raise_for_status()
        collections = response.json()
        
        for collection in collections:
            if collection.get("name") == KNOWLEDGE_COLLECTION_NAME:
                logger.info(f"Found existing collection: {collection['id']}")
                return collection["id"]
        
        # Create new collection
        logger.info(f"Creating new knowledge collection: {KNOWLEDGE_COLLECTION_NAME}")
        payload = {
            "name": KNOWLEDGE_COLLECTION_NAME,
            "description": f"Daily RAG document ingestion - {datetime.now().isoformat()}"
        }
        
        response = requests.post(f"{OPEN_WEBUI_URL}/api/v1/knowledge/create", 
                               json=payload, headers=headers)
        response.raise_for_status()
        collection_data = response.json()
        logger.success(f"Created collection: {collection_data['id']}")
        return collection_data["id"]
        
    except Exception as e:
        logger.error(f"Failed to get/create knowledge collection: {e}")
        return None

def upload_and_process_file(file_path: Path, collection_id: str) -> bool:
    """Upload a file and add it to the knowledge collection"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        # Read file content to check if it's valid
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        if len(content.strip()) < 50:  # Skip files with minimal content
            logger.warning(f"Skipping {file_path.name} - insufficient content ({len(content)} chars)")
            return False
        
        # Upload file
        logger.info(f"Uploading {file_path.name}...")
        with open(file_path, 'rb') as f:
            files = {"file": (file_path.name, f, "text/plain")}
            response = requests.post(f"{OPEN_WEBUI_URL}/api/v1/files/", 
                                   files=files, headers=headers)
            response.raise_for_status()
        
        file_data = response.json()
        file_id = file_data.get("id")
        
        if not file_id:
            logger.error(f"Failed to get file ID for {file_path.name}")
            return False
        
        logger.success(f"Uploaded {file_path.name} with ID: {file_id}")
        
        # Add file to knowledge collection
        logger.info(f"Adding file {file_id} to knowledge collection...")
        add_url = f"{OPEN_WEBUI_URL}/api/v1/knowledge/{collection_id}/file/add"
        add_payload = {"file_id": file_id}
        
        response = requests.post(add_url, json=add_payload, headers=headers)
        response.raise_for_status()
        
        logger.success(f"Successfully added {file_path.name} to knowledge collection!")
        save_processed_file(file_path.name)
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {file_path.name}: {e}")
        return False

def main():
    """Main daily ingestion process"""
    if not API_KEY:
        logger.error("OPEN_WEBUI_API_KEY environment variable not set")
        sys.exit(1)
    
    logger.info("Starting daily RAG ingestion...")
    
    # Get collection ID
    collection_id = get_or_create_knowledge_collection()
    if not collection_id:
        logger.error("Cannot proceed without knowledge collection")
        sys.exit(1)
    
    # Find new files
    new_files = get_new_files_since_yesterday()
    logger.info(f"Found {len(new_files)} new files to process")
    
    if not new_files:
        logger.info("No new files to process")
        return
    
    # Process each file
    successful = 0
    for file_path in new_files:
        if upload_and_process_file(file_path, collection_id):
            successful += 1
        time.sleep(1)  # Rate limiting
    
    logger.info(f"Daily ingestion complete: {successful}/{len(new_files)} files processed")

if __name__ == "__main__":
    main()