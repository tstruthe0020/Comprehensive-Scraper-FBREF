import React, { useState } from 'react';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  const handleDemo = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${backendUrl}/api/demo-scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (data.success) {
        setResult(data);
      } else {
        setError(data.message || 'Demo failed');
      }
    } catch (err) {
      setError('Network error: Unable to connect to the server');
    } finally {
      setLoading(false);
    }
  };
    e.preventDefault();
    if (!url.trim()) {
      setError('Please enter a valid FBREF URL');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${backendUrl}/api/scrape-fbref`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      const data = await response.json();

      if (data.success) {
        setResult(data);
      } else {
        setError(data.message || 'Failed to scrape the webpage');
      }
    } catch (err) {
      setError('Network error: Unable to connect to the server');
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = () => {
    if (result && result.csv_data) {
      const blob = new Blob([result.csv_data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'fbref_match_data.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  const clearResults = () => {
    setResult(null);
    setError('');
    setUrl('');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            FBREF Fixture Scraper
          </h1>
          <p className="text-gray-600 mb-6">
            Extract match report links from FBREF fixture/schedule pages and generate CSV data for analysis.
          </p>

          <form onSubmit={handleSubmit} className="mb-6">
            <div className="mb-4">
              <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                FBREF Fixture List URL
              </label>
              <input
                type="url"
                id="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              />
            </div>
            
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-md font-medium transition-colors duration-200"
              >
                {loading ? 'Scraping...' : 'Extract Links'}
              </button>
              
              {result && (
                <button
                  type="button"
                  onClick={clearResults}
                  className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-md font-medium transition-colors duration-200"
                >
                  Clear
                </button>
              )}
            </div>
          </form>

          {/* Example URLs */}
          <div className="mb-6 p-4 bg-gray-50 rounded-md">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Example URLs:</h3>
            <div className="space-y-1 text-sm">
              <div>
                <strong>Current Season:</strong>
                <br />
                <code className="text-blue-600">https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures</code>
              </div>
              <div>
                <strong>Previous Seasons:</strong>
                <br />
                <code className="text-blue-600">https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures</code>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <h3 className="text-sm font-medium text-red-800 mb-1">Error:</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-6">
              <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  ✅ {result.message}
                </h3>
                <div className="flex gap-3">
                  <button
                    onClick={downloadCSV}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200"
                  >
                    📥 Download CSV
                  </button>
                  <span className="text-sm text-green-700 py-2">
                    {result.links.length} match links found
                  </span>
                </div>
              </div>

              {/* Links Preview */}
              <div className="bg-gray-50 rounded-md p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">
                  Extracted Match Report Links ({result.links.length})
                </h3>
                <div className="max-h-64 overflow-y-auto border border-gray-200 rounded bg-white">
                  {result.links.map((link, index) => (
                    <div key={index} className="p-2 border-b border-gray-100 last:border-b-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">#{index + 1}</span>
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 text-sm underline flex-1 ml-3 truncate"
                        >
                          {link}
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;