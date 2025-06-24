import os
import asyncio
import uuid
import logging
import threading
import requests
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import config
from web_scraper import scrape_and_save_url
from pdf_processor import process_pdf
from vector_db import add_document_to_webui

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Ensure the output directory exists
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_and_process_pdf(pdf_url: str) -> Path | None:
    """Downloads a PDF from a URL, saves it, processes it, and returns the output path."""
    try:
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        original_filename = secure_filename(Path(pdf_url).name) or "downloaded.pdf"
        if not original_filename.endswith('.pdf'):
            original_filename += '.pdf'

        temp_path = config.OUTPUT_DIR / f"temp_{uuid.uuid4()}.pdf"
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Temporarily saved downloaded PDF to {temp_path}")
        return process_pdf(temp_path, original_filename)
    except requests.RequestException as e:
        logger.error(f"Failed to download PDF from {pdf_url}: {e}")
    except Exception as e:
        logger.error(f"Error processing PDF from {pdf_url}: {e}")
    return None

def process_rag_request_background(urls: list, pdf_urls: list):
    """Runs the scraping and processing in a background thread and ingests to WebUI."""
    logger.info(f"Background task started for {len(urls)} URLs and {len(pdf_urls)} PDFs.")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Process URLs asynchronously
    scraping_tasks = [scrape_and_save_url(url) for url in urls]
    if scraping_tasks:
        # This will return a list of Paths or Nones
        processed_files = loop.run_until_complete(asyncio.gather(*scraping_tasks))
        for file_path in processed_files:
            if file_path:
                add_document_to_webui(file_path)

    # Process PDFs sequentially
    for pdf_url in pdf_urls:
        file_path = download_and_process_pdf(pdf_url)
        if file_path:
            add_document_to_webui(file_path)

    logger.info("Background RAG update task finished.")

@app.route('/api/rag-webhook', methods=['POST'])
def rag_webhook_endpoint():
    """Webhook for n8n to trigger RAG content updates from URLs and PDFs."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    urls = data.get('urls', [])
    pdf_urls = data.get('pdfs', [])

    if not isinstance(urls, list) or not isinstance(pdf_urls, list):
        return jsonify({"error": "'urls' and 'pdfs' must be lists"}), 400

    if not urls and not pdf_urls:
        return jsonify({"error": "Payload must contain 'urls' and/or 'pdfs'"}), 400

    thread = threading.Thread(target=process_rag_request_background, args=(urls, pdf_urls))
    thread.start()

    return jsonify({
        "status": "accepted",
        "message": f"Task accepted to process {len(urls)} URLs and {len(pdf_urls)} PDFs."
    }), 202

@app.route('/api/files', methods=['GET'])
def list_files():
    """Lists all processed .txt files, sorted by modification time."""
    try:
        files = sorted(
            config.OUTPUT_DIR.glob('*.txt'),
            key=os.path.getmtime,
            reverse=True
        )
        return jsonify([f.name for f in files])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Serves a processed text file for download."""
    try:
        return send_from_directory(
            config.OUTPUT_DIR,
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404


@app.route('/api/scrape', methods=['POST'])
def scrape_url_endpoint():
    """API endpoint to trigger web scraping for a list of URLs."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    urls = data.get('urls', [])
    if not isinstance(urls, list):
        return jsonify({"error": "'urls' must be a list"}), 400

    if not urls:
        return jsonify({"error": "Payload must contain 'urls'"}), 400

    # Use the existing background processing function, passing an empty list for pdf_urls
    thread = threading.Thread(target=process_rag_request_background, args=(urls, []))
    thread.start()

    return jsonify({
        "status": "accepted",
        "message": f"Task accepted to process {len(urls)} URLs."
    }), 202

@app.route('/api/upload', methods=['POST'])
def upload_pdf_endpoint():
    """API endpoint to handle direct PDF file uploads."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file and file.filename.endswith('.pdf'):
        original_filename = secure_filename(file.filename)
        temp_path = config.OUTPUT_DIR / f"temp_{uuid.uuid4()}.pdf"
        try:
            file.save(temp_path)
            output_path = process_pdf(temp_path, original_filename)
            if output_path:
                # Run ingestion in a background thread
                thread = threading.Thread(target=add_document_to_webui, args=(output_path,))
                thread.start()
                return jsonify({"message": f"Successfully processed '{original_filename}' and started ingestion."}), 200
            else:
                return jsonify({"error": "Failed to process PDF file."}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get file statistics"""
    import datetime
    files = list(config.OUTPUT_DIR.glob("*.txt"))
    total_size = sum(f.stat().st_size for f in files)
    
    # Find the most recently modified file
    latest_file = None
    latest_time = None
    if files:
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        latest_time = datetime.datetime.fromtimestamp(latest_file.stat().st_mtime)
    
    result = {
        "file_count": len(files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024*1024), 1),
        "total_size_human": f"{total_size / (1024*1024):.1f} MB" if total_size > 1024*1024 else f"{total_size / 1024:.1f} KB"
    }
    
    if latest_file and latest_time:
        result["last_updated"] = latest_time.strftime("%Y-%m-%d %H:%M:%S")
        result["last_updated_file"] = latest_file.name
        result["last_updated_relative"] = get_relative_time(latest_time)
    else:
        result["last_updated"] = "No files found"
        result["last_updated_file"] = None
        result["last_updated_relative"] = "N/A"
    
    return jsonify(result)

def get_relative_time(timestamp):
    """Get human-readable relative time"""
    import datetime
    now = datetime.datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

@app.route('/', methods=['GET'])
def index():
    """Main page for RAG Scraper API"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AutoLlama API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .endpoint { 
                background: #f4f4f4; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
                border: 2px solid transparent;
                transition: all 0.3s ease;
            }
            .endpoint.clickable { 
                cursor: pointer; 
                border-color: #0066cc;
            }
            .endpoint.clickable:hover { 
                background: #e6f3ff; 
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,102,204,0.2);
            }
            .method { color: #0066cc; font-weight: bold; }
            .method.get { background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; }
            .method.post { background: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; }
            .status { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .result { 
                background: #f8f9fa; 
                border: 1px solid #dee2e6; 
                border-radius: 5px; 
                padding: 15px; 
                margin: 15px 0;
                max-height: 400px;
                overflow-y: auto;
            }
            .result h4 { margin: 0 0 10px 0; color: #495057; }
            .file-list { 
                max-height: 300px; 
                overflow-y: auto; 
                background: white; 
                padding: 10px; 
                border-radius: 3px;
            }
            .file-item { 
                padding: 5px; 
                border-bottom: 1px solid #eee; 
                cursor: pointer;
                transition: background 0.2s;
            }
            .file-item:hover { background: #f8f9fa; }
            .file-item:last-child { border-bottom: none; }
            .loading { color: #666; font-style: italic; }
            .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 3px; }
            .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦙 AutoLlama API</h1>
            <div class="status" id="statusBar">
                <strong>✅ API Status:</strong> Online and Ready<br>
                <strong>🔄 Processing:</strong> Real-time (every 1 minute)<br>
                <strong>📊 Files Available:</strong> """ + str(len(list(config.OUTPUT_DIR.glob("*.txt")))) + """ documents<br>
                <strong>💾 Total Space:</strong> """ + f"{sum(f.stat().st_size for f in config.OUTPUT_DIR.glob('*.txt')) / (1024*1024):.1f} MB" + """<br>
                <strong>🕒 Last Updated:</strong> <span id="lastUpdated">Loading...</span>
            </div>
            
            <h2>📚 Available Endpoints</h2>
            
            <div class="endpoint clickable" onclick="fetchFiles()">
                <span class="method get">GET</span> <strong>/api/files</strong><br>
                <em>List all processed files</em><br>
                <small>💡 Click to fetch and display all files</small>
            </div>
            
            <div class="endpoint clickable" onclick="fetchStats()">
                <span class="method get">GET</span> <strong>/api/stats</strong><br>
                <em>Get file statistics and storage info</em><br>
                <small>💡 Click to view detailed file statistics</small>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/api/scrape</strong><br>
                <em>Scrape URLs and process content</em><br>
                <small>Body: {"urls": ["https://example.com"]}</small>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/api/rag-webhook</strong><br>
                <em>n8n integration webhook</em><br>
                <small>Body: {"urls": [...], "pdfs": [...]}</small>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/api/upload</strong><br>
                <em>Upload PDF files for processing</em>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/api/download/&lt;filename&gt;</strong><br>
                <em>Download processed files</em>
            </div>
            
            <!-- Results container -->
            <div id="results"></div>
            
            <h2>🔗 Related Services</h2>
            <p><strong>OpenWebUI:</strong> <a href="https://o.llamagic.com">o.llamagic.com</a> - RAG Chat Interface</p>
            
            <h2>📖 Documentation</h2>
            <p>View the complete documentation on <a href="https://github.com/snedea/autollama">GitHub</a></p>
        </div>

        <script>
            async function fetchFiles() {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="result"><div class="loading">🔄 Fetching files...</div></div>';
                
                try {
                    const response = await fetch('/api/files');
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const files = await response.json();
                    displayFiles(files);
                    updateStats(); // Update stats after fetching files
                } catch (error) {
                    resultsDiv.innerHTML = `
                        <div class="result">
                            <div class="error">❌ Error: ${error.message}</div>
                        </div>
                    `;
                }
            }
            
            async function fetchStats() {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="result"><div class="loading">🔄 Fetching statistics...</div></div>';
                
                try {
                    const response = await fetch('/api/stats');
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const stats = await response.json();
                    displayStats(stats);
                    updateStatusBar(stats); // Update the status bar with latest stats
                } catch (error) {
                    resultsDiv.innerHTML = `
                        <div class="result">
                            <div class="error">❌ Error: ${error.message}</div>
                        </div>
                    `;
                }
            }
            
            async function updateStats() {
                try {
                    const response = await fetch('/api/stats');
                    if (response.ok) {
                        const stats = await response.json();
                        updateStatusBar(stats);
                    }
                } catch (error) {
                    // Silently fail for background updates
                }
            }
            
            function displayStats(stats) {
                const resultsDiv = document.getElementById('results');
                
                const latestFileInfo = stats.last_updated_file ? 
                    `<strong>📄 Latest File:</strong> ${stats.last_updated_file}<br>` : '';
                
                resultsDiv.innerHTML = `
                    <div class="result">
                        <h4>📊 File Statistics</h4>
                        <div class="success">
                            <strong>📁 Total Files:</strong> ${stats.file_count} documents<br>
                            <strong>💾 Total Storage:</strong> ${stats.total_size_human}<br>
                            <strong>📏 Raw Size:</strong> ${stats.total_size_bytes.toLocaleString()} bytes<br>
                            <strong>🗂️ Average File Size:</strong> ${stats.file_count > 0 ? (stats.total_size_bytes / stats.file_count / 1024).toFixed(1) + ' KB' : '0 KB'}<br>
                            <strong>🕒 Last Updated:</strong> ${stats.last_updated} (${stats.last_updated_relative})<br>
                            ${latestFileInfo}
                        </div>
                    </div>
                `;
            }
            
            function updateStatusBar(stats) {
                // Update the status bar with fresh statistics
                const statusDiv = document.querySelector('.status');
                if (statusDiv) {
                    statusDiv.innerHTML = `
                        <strong>✅ API Status:</strong> Online and Ready<br>
                        <strong>🔄 Processing:</strong> Real-time (every 1 minute)<br>
                        <strong>📊 Files Available:</strong> ${stats.file_count} documents<br>
                        <strong>💾 Total Space:</strong> ${stats.total_size_human}<br>
                        <strong>🕒 Last Updated:</strong> ${stats.last_updated_relative}
                    `;
                }
            }
            
            function displayFiles(files) {
                const resultsDiv = document.getElementById('results');
                
                if (!files || files.length === 0) {
                    resultsDiv.innerHTML = `
                        <div class="result">
                            <h4>📁 Files (0)</h4>
                            <div class="success">No files found.</div>
                        </div>
                    `;
                    return;
                }
                
                const fileList = files.map(file => `
                    <div class="file-item" onclick="downloadFile('${file}')">
                        📄 ${file}
                    </div>
                `).join('');
                
                resultsDiv.innerHTML = `
                    <div class="result">
                        <h4>📁 Files (${files.length})</h4>
                        <div class="success">✅ Found ${files.length} processed files. Click any file to download.</div>
                        <div class="file-list">
                            ${fileList}
                        </div>
                    </div>
                `;
            }
            
            function downloadFile(filename) {
                const url = `/api/download/${encodeURIComponent(filename)}`;
                window.open(url, '_blank');
            }
            
            // Load initial stats when page loads
            window.addEventListener('load', () => {
                updateStats();
            });
            
            // Auto-refresh files every 30 seconds if results are showing
            setInterval(() => {
                const resultsDiv = document.getElementById('results');
                if (resultsDiv.innerHTML.trim() !== '') {
                    // Refresh whatever is currently displayed
                    if (resultsDiv.innerHTML.includes('File Statistics')) {
                        fetchStats();
                    } else {
                        fetchFiles();
                    }
                } else {
                    // Always keep the status bar updated
                    updateStats();
                }
            }, 30000);
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
