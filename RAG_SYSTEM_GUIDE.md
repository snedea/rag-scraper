# RAG System Setup Guide

Your RAG (Retrieval-Augmented Generation) system is now configured and running! Here's how everything works:

## 🎯 What's Working

✅ **Real-time File Processing**: New documents are automatically uploaded to OpenWebUI every 1 minute  
✅ **Junk File Filtering**: Files with minimal content (< 50 chars) are automatically discarded  
✅ **Knowledge Collection**: "rag_documents" collection is created and ready  
✅ **File Upload**: 109 quality documents have been uploaded to OpenWebUI  

## 🔧 Manual Steps Required

### Add Files to Knowledge Collection

1. **Access OpenWebUI**: Go to `https://o.llamagic.com`
2. **Navigate to Knowledge**: Look for "Knowledge" or "Knowledge Collections" in the menu
3. **Find "rag_documents"**: You should see your knowledge collection
4. **Add Files**: Select and add the uploaded files to the collection
5. **Wait for Processing**: OpenWebUI will process the files for vector search

### Test the RAG System

Once files are added to the knowledge collection:

1. **Start a new chat** in OpenWebUI
2. **Use the # command**: Type `#` and you should see "rag_documents" as an option
3. **Select it**: This enables RAG for your conversation
4. **Ask questions**: Ask about content from your scraped documents

Example queries:
- "What does the document say about guitar practice routines?"
- "Tell me about the Erie Canal's history"
- "What information do you have about beekeeping?"

## 🔄 Automated Real-time Processing

### How It Works

- **Cron Job**: Runs every 1 minute
- **File Scanning**: Checks for new/modified files in the last 24 hours
- **Quality Filter**: Only processes files with substantial content (≥50 characters)
- **Upload**: Automatically uploads quality files to OpenWebUI
- **Tracking**: Maintains a log of processed files to avoid duplicates

### Manual Commands

```bash
# Run ingestion manually
cd /home/chuck/rag_scraper
docker exec rag_scraper-backend-1 python3 /app/daily_ingest.py

# Check cron status
crontab -l

# View processing logs
tail -f /tmp/daily_ingest.log

# Clean up junk files manually
docker exec rag_scraper-backend-1 python3 /app/cleanup_junk_files.py --delete
```

## 📁 File Structure

```
/home/chuck/rag_scraper/
├── processed_files/           # Scraped documents (109 files)
├── daily_ingest.py           # Daily processing script
├── cleanup_junk_files.py     # Junk file cleanup utility
├── setup_daily_cron.sh       # Cron job setup script
├── daily_ingest_tracker.txt  # Tracks processed files
└── docker-compose.yml        # Container configuration
```

## 🚨 Troubleshooting

### Files Not Appearing in Knowledge Collection
- Check that files are uploaded: Access OpenWebUI → Files
- Manually add files to knowledge collection via the UI
- Verify collection name is "rag_documents"

### Daily Processing Not Working
```bash
# Check cron job exists
crontab -l

# Test manual run
docker exec rag_scraper-backend-1 python3 /app/daily_ingest.py

# Check Docker containers are running
docker ps
```

### RAG Search Not Working
- Ensure files are added to the knowledge collection (not just uploaded)
- Try using `#rag_documents` in your chat
- Check that the collection has been processed (may take a few minutes)

## 🎛️ Configuration

### Environment Variables
- `OPEN_WEBUI_API_KEY`: Set in `/home/chuck/rag_scraper/.env`
- `OPEN_WEBUI_URL`: Points to OpenWebUI container

### Customization
- **Processing Schedule**: Edit cron job with `crontab -e`
- **Minimum File Size**: Modify `min_content_length` in scripts
- **Collection Name**: Change `KNOWLEDGE_COLLECTION_NAME` in `daily_ingest.py`

## 🔗 Access Points

- **OpenWebUI**: https://o.llamagic.com
- **RAG API**: https://r.llamagic.com/api/
- **Processing Logs**: `/tmp/daily_ingest.log`

Your RAG system is ready! Just add the uploaded files to the knowledge collection and start using the `#` command to search your documents.