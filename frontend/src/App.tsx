import { useState, useEffect, useRef, type FormEvent, type ChangeEvent } from 'react';

const API_BASE_URL = ''; // Use relative paths for API calls

function App() {
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [processedFiles, setProcessedFiles] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isScraping, setIsScraping] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchFiles = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/files`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to fetch files' }));
        throw new Error(errorData.error || 'Failed to fetch files');
      }
      const data = await response.json();
      setProcessedFiles(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred while fetching files.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleUrlSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setError('Please enter a URL.');
      return;
    }
    setIsScraping(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: trimmedUrl }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to scrape URL.');
      }

      setMessage(result.message);
      setUrl('');
      await fetchFiles();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred during scraping.');
      }
    } finally {
      setIsScraping(false);
    }
  };

  const handleFileSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF file to upload.');
      return;
    }
    setIsUploading(true);
    setError(null);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to process PDF.');
      }

      setMessage(result.message);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      await fetchFiles();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred during PDF processing.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const isBusy = isScraping || isUploading;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 font-sans">
      <header className="sticky top-0 z-10 bg-slate-800/70 backdrop-blur-sm p-4 shadow-lg border-b border-slate-700">
        <h1 className="text-3xl font-bold text-sky-400">RAG Content Scraper</h1>
        <p className="text-slate-400 mt-1">Scrape web pages or process PDFs into clean text for RAG ingestion.</p>
      </header>

      <main className="p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scrape a Website Card */}
        <div className="bg-slate-800/50 p-6 rounded-xl shadow-xl border border-slate-700">
          <h2 className="text-2xl font-semibold mb-4 text-sky-300">Scrape a Website</h2>
          <form onSubmit={handleUrlSubmit}>
            <label htmlFor="url-input" className="block mb-2 font-medium text-slate-300">URL</label>
            <input
              id="url-input"
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              required
              disabled={isBusy}
              className="w-full p-2 bg-slate-700 border border-slate-600 rounded-md focus:ring-2 focus:ring-sky-500 focus:outline-none disabled:opacity-50 transition-colors"
            />
            <button type="submit" disabled={isBusy} className="mt-4 w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 disabled:bg-sky-800 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-sky-500/50">
              {isScraping ? 'Scraping...' : 'Scrape URL'}
            </button>
          </form>
        </div>

        {/* Process a PDF Card */}
        <div className="bg-slate-800/50 p-6 rounded-xl shadow-xl border border-slate-700">
          <h2 className="text-2xl font-semibold mb-4 text-sky-300">Process a PDF</h2>
          <form onSubmit={handleFileSubmit}>
            <label className="block mb-2 font-medium text-slate-300">PDF File</label>
            <div className="flex items-center space-x-4">
              <button type="button" onClick={handleFileSelect} disabled={isBusy} className="bg-slate-600 hover:bg-slate-500 text-white font-bold py-2 px-4 rounded-md transition duration-300 disabled:bg-slate-700 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-slate-500/50">
                Choose File
              </button>
              <span className="text-slate-400 truncate">{file ? file.name : 'No file selected'}</span>
              <input type="file" accept=".pdf" ref={fileInputRef} onChange={onFileChange} style={{ display: 'none' }} id="file-upload" />
            </div>
            <button type="submit" disabled={isBusy || !file} className="mt-4 w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 disabled:bg-sky-800 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-sky-500/50">
              {isUploading ? 'Processing...' : 'Process PDF'}
            </button>
          </form>
        </div>
      </main>

      {/* Notifications */}
      <div className="px-4 sm:px-6 pb-4 space-y-4">
        {message && (
          <div className="bg-green-500/10 border border-green-500/30 text-green-200 px-4 py-3 rounded-md relative flex justify-between items-center" role="alert">
            <span className="block sm:inline">{message}</span>
            <button onClick={() => setMessage(null)} className="-mr-1 p-1 rounded-md hover:bg-green-500/20">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
            </button>
          </div>
        )}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-200 px-4 py-3 rounded-md relative flex justify-between items-center" role="alert">
            <span className="block sm:inline">{error}</span>
            <button onClick={() => setError(null)} className="-mr-1 p-1 rounded-md hover:bg-red-500/20">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
            </button>
          </div>
        )}
      </div>

      {/* Processed Files List */}
      <div className="px-4 sm:px-6 pb-4">
        <div className="bg-slate-800/50 p-6 rounded-xl shadow-xl border border-slate-700">
          <h2 className="text-2xl font-semibold mb-4 text-sky-300">Processed Files</h2>
          {isLoading ? (
            <p className="text-slate-400">Loading files...</p>
          ) : processedFiles.length > 0 ? (
            <ul className="space-y-3">
              {processedFiles.map((filename) => (
                <li key={filename} className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg border border-slate-600">
                  <span className="truncate mr-4 font-mono text-sm">{filename}</span>
                  <a href={`${API_BASE_URL}/api/download/${filename}`} download className="flex-shrink-0 bg-slate-600 hover:bg-slate-500 text-white font-bold py-1 px-3 rounded-md text-sm transition duration-300 focus:outline-none focus:ring-4 focus:ring-slate-500/50">
                    Download
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400">No files found. Scrape a URL or upload a PDF to get started.</p>
          )}
        </div>
      </div>
      <footer className="text-center mt-8 pb-4">
        <p className="text-xs text-slate-500">Version 1.2.0</p>
      </footer>
    </div>
  );
}

export default App;

