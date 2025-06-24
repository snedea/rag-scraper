import os
import requests
from pathlib import Path
from loguru import logger
from typing import Optional

# Get Open WebUI configuration from environment variables
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://openwebui:8080")
COLLECTION_NAME = "rag_documents"

def _get_collection_id(collection_name: str, headers: dict) -> Optional[str]:
    """
    Gets the ID of a knowledge base collection by its name.
    """
    url = f"{OPEN_WEBUI_URL}/api/v1/knowledge/"
    logger.info(f"Attempting to find collection '{collection_name}'...")
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        collections = response.json()
        for collection in collections:
            if collection.get("name") == collection_name:
                collection_id = collection.get("id")
                logger.success(f"Found collection '{collection_name}' with ID: {collection_id}")
                return collection_id
        logger.warning(f"Collection '{collection_name}' not found.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get collections: {e}")
        logger.error(f"Response body: {e.response.text if e.response else 'No response'}")
        return None

def _create_collection(collection_name: str, headers: dict) -> Optional[str]:
    """
    Creates a new knowledge base collection.
    """
    url = f"{OPEN_WEBUI_URL}/api/v1/knowledge/create"
    payload = {
        "name": collection_name,
        "description": f"RAG documents collection: {collection_name}"
    }
    logger.info(f"Creating collection '{collection_name}'...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        collection_id = data.get("id")
        if collection_id:
            logger.success(f"Successfully created collection '{collection_name}' with ID: {collection_id}")
            return collection_id
        else:
            logger.error(f"Collection created, but no ID was returned. Response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create collection: {e}")
        logger.error(f"Response body: {e.response.text if e.response else 'No response'}")
        return None

def _upload_file(file_path: Path, headers: dict) -> Optional[str]:
    """
    Uploads a file to the Open WebUI files endpoint.
    """
    url = f"{OPEN_WEBUI_URL}/api/v1/files/"
    logger.info(f"Uploading {file_path.name} to Open WebUI...")
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/plain")}
            response = requests.post(url, files=files, headers=headers, timeout=60)
            response.raise_for_status()
        data = response.json()
        doc_id = data.get("id")
        if doc_id:
            logger.success(f"Successfully uploaded file. Document ID: {doc_id}")
            return doc_id
        else:
            logger.error(f"File uploaded, but no document ID was returned. Response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload file {file_path.name}: {e}")
        logger.error(f"Response body: {e.response.text if e.response else 'No response'}")
        return None

def _add_file_to_collection(collection_id: str, doc_id: str, headers: dict) -> bool:
    """
    Adds a previously uploaded document to the specified RAG collection.
    """
    url = f"{OPEN_WEBUI_URL}/api/v1/knowledge/{collection_id}/file/add"
    payload = {"file_id": doc_id}
    logger.info(f"Adding document {doc_id} to collection ID {collection_id}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        logger.success(f"Successfully added document {doc_id} to collection.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to add document {doc_id} to collection: {e}")
        logger.error(f"Response body: {e.response.text if e.response else 'No response'}")
        return False

def add_document_to_webui(file_path: Path):
    """
    Processes a single text file and ingests it into Open WebUI's RAG.
    """
    logger.info(f"Starting ingestion process for {file_path.name}...")
    
    api_key = os.getenv("OPEN_WEBUI_API_KEY")
    if not api_key:
        logger.error("OPEN_WEBUI_API_KEY not set. Halting ingestion.")
        return
    headers = {"Authorization": f"Bearer {api_key}"}

    # Step 1: Get the collection ID, or create it if it doesn't exist.
    collection_id = _get_collection_id(COLLECTION_NAME, headers)
    if not collection_id:
        collection_id = _create_collection(COLLECTION_NAME, headers)
    
    if not collection_id:
        logger.error(f"Could not find or create collection '{COLLECTION_NAME}'. Halting.")
        return

    # Step 2: Upload the file to get a document ID
    document_id = _upload_file(file_path, headers)
    if not document_id:
        logger.error("Halting ingestion process due to upload failure.")
        return

    # Step 3: Add the document to the collection
    _add_file_to_collection(collection_id, document_id, headers)
