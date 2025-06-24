#!/bin/bash
# Setup frequent cron job for RAG document ingestion (every 1 minute)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_CMD="* * * * * cd $SCRIPT_DIR && docker exec rag_scraper-backend-1 python3 /app/daily_ingest.py >> /tmp/daily_ingest.log 2>&1"

echo "Setting up frequent cron job for RAG ingestion (every 1 minute)..."
echo "Script directory: $SCRIPT_DIR"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_ingest.py"; then
    echo "RAG ingestion cron job already exists"
    crontab -l 2>/dev/null | grep "daily_ingest.py"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Added frequent cron job:"
    echo "$CRON_CMD"
fi

echo ""
echo "Cron job will run every 1 minute"
echo "Log file: /tmp/daily_ingest.log"
echo ""
echo "To manually run the ingestion:"
echo "cd $SCRIPT_DIR && docker-compose exec backend python3 daily_ingest.py"
echo ""
echo "To remove the cron job:"
echo "crontab -e  # then delete the line containing 'daily_ingest.py'"