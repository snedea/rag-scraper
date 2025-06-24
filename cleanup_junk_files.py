#!/usr/bin/env python3
"""
Cleanup script to remove junk files with minimal content from scraped data
"""
import os
from pathlib import Path
from loguru import logger

def cleanup_junk_files(directory: Path, min_content_length: int = 50, dry_run: bool = True):
    """
    Remove files with minimal content that are likely scraping errors
    
    Args:
        directory: Directory to scan for files
        min_content_length: Minimum character count to keep file
        dry_run: If True, only report what would be deleted
    """
    txt_files = list(directory.glob("*.txt"))
    logger.info(f"Scanning {len(txt_files)} text files in {directory}")
    
    junk_files = []
    total_size_removed = 0
    
    for file_path in txt_files:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            content_length = len(content.strip())
            
            if content_length < min_content_length:
                file_size = file_path.stat().st_size
                junk_files.append((file_path, content_length, file_size))
                total_size_removed += file_size
                
                if dry_run:
                    logger.info(f"WOULD DELETE: {file_path.name} ({content_length} chars, {file_size} bytes)")
                else:
                    file_path.unlink()
                    logger.info(f"DELETED: {file_path.name} ({content_length} chars, {file_size} bytes)")
                    
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
    
    action = "Would delete" if dry_run else "Deleted"
    logger.info(f"{action} {len(junk_files)} junk files, saving {total_size_removed:,} bytes")
    
    if junk_files and dry_run:
        logger.info("To actually delete these files, run with --delete flag")
    
    return len(junk_files)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup junk files from RAG scraping")
    parser.add_argument("--directory", "-d", type=Path, default=Path("processed_files"),
                       help="Directory to scan (default: processed_files)")
    parser.add_argument("--min-length", "-m", type=int, default=50,
                       help="Minimum content length to keep file (default: 50)")
    parser.add_argument("--delete", action="store_true",
                       help="Actually delete files (default: dry run)")
    
    args = parser.parse_args()
    
    if not args.directory.exists():
        logger.error(f"Directory {args.directory} does not exist")
        return
    
    logger.info(f"Cleanup mode: {'DELETE' if args.delete else 'DRY RUN'}")
    cleanup_junk_files(args.directory, args.min_length, dry_run=not args.delete)

if __name__ == "__main__":
    main()