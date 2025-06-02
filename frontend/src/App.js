import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [urls, setUrls] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [enhancing, setEnhancing] = useState(false);
  const [enhancementAvailable, setEnhancementAvailable] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Check if enhancement is available on component mount
  useEffect(() => {
    checkEnhancementAvailability();
  }, []);

  const checkEnhancementAvailability = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/check-enhancement`);
      const data = await response.json();
      setEnhancementAvailable(data.available);
    } catch (err) {
      console.log('Enhancement check failed:', err);
      setEnhancementAvailable(false);
    }
  };

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!urls.trim()) {
      setError('Please enter at least one FBREF URL');
      return;
    }

    // Parse URLs from textarea (one per line or comma-separated)
    const urlList = urls
      .split(/[\n,]/)
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (urlList.length === 0) {
      setError('Please enter valid FBREF URLs');
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
        body: JSON.stringify({ urls: urlList }),
      });

      const data = await response.json();

      if (data.success) {
        setResult(data);
      } else {
        setError(data.message || 'Failed to scrape the webpages');
      }
    } catch (err) {
      setError('Network error: Unable to connect to the server');
    } finally {
      setLoading(false);
    }
  };

  const enhanceExcel = async () => {
    if (!result || !result.excel_data || enhancing) return;

    setEnhancing(true);
    try {
      const response = await fetch(`${backendUrl}/api/enhance-excel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          excel_data: result.excel_data,
          filename: result.filename
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Update result with enhanced data
        setResult({
          ...result,
          excel_data: data.excel_data,
          filename: data.filename,
          message: data.message,
          enhancement_results: data.enhancement_results
        });
      } else {
        setError(`Enhancement failed: ${data.message}`);
      }
    } catch (err) {
      setError('Enhancement error: Unable to connect to the server');
    } finally {
      setEnhancing(false);
    }
  };

  const downloadExcel = () => {
    if (result && result.excel_data) {
      const byteCharacters = atob(result.excel_data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = result.filename || 'fbref_compiled_match_data.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  const clearResults = () => {
    setResult(null);
    setError('');
    setUrls('');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            FBREF Multi-Season Scraper
          </h1>
          <p className="text-gray-600 mb-6">
            Extract match report links from multiple FBREF fixture/schedule pages and compile all data into a structured Excel file with separate sheets for each match.
          </p>

          <form onSubmit={handleSubmit} className="mb-6">
            <div className="mb-4">
              <label htmlFor="urls" className="block text-sm font-medium text-gray-700 mb-2">
                FBREF Fixture URLs (one per line or comma-separated)
              </label>
              <textarea
                id="urls"
                value={urls}
                onChange={(e) => setUrls(e.target.value)}
                placeholder={`https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures
https://fbref.com/en/comps/9/2022-2023/schedule/2022-2023-Premier-League-Scores-and-Fixtures
https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures`}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-24 resize-y"
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter multiple URLs to compile data from different seasons
              </p>
            </div>
            
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-md font-medium transition-colors duration-200"
              >
                {loading ? 'Scraping Seasons...' : 'Extract Links'}
              </button>
              
              <button
                type="button"
                onClick={handleDemo}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-6 py-2 rounded-md font-medium transition-colors duration-200"
              >
                {loading ? 'Loading...' : 'Try Demo'}
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
            <h3 className="text-sm font-medium text-gray-700 mb-2">Example URL formats:</h3>
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
              <div>
                <strong>Different Leagues:</strong>
                <br />
                <code className="text-blue-600">https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures</code>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <h3 className="text-sm font-medium text-red-800 mb-1">Error:</h3>
              <p className="text-sm text-red-700 whitespace-pre-line">{error}</p>
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-6">
              <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  ✅ {result.message}
                </h3>
                <div className="flex gap-3 items-center">
                  <button
                    onClick={downloadExcel}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200"
                  >
                    📥 Download Compiled Excel
                  </button>
                  <span className="text-sm text-green-700">
                    {result.total_links} total match links from {result.seasons?.length || 0} seasons
                  </span>
                </div>
              </div>

              {/* Season Results */}
              {result.seasons && result.seasons.length > 0 && (
                <div className="bg-gray-50 rounded-md p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">
                    Season Results
                  </h3>
                  <div className="space-y-3">
                    {result.seasons.map((season, index) => (
                      <div key={index} className={`p-3 rounded border-l-4 ${
                        season.success 
                          ? 'bg-green-50 border-green-500' 
                          : 'bg-red-50 border-red-500'
                      }`}>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">
                            {season.season_name}
                          </h4>
                          <span className={`text-sm px-2 py-1 rounded ${
                            season.success 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {season.success ? `${season.links.length} links` : 'Failed'}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">{season.message}</p>
                        <p className="text-xs text-gray-500 truncate">{season.url}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* All Links Preview */}
              {result.seasons && (
                <div className="bg-gray-50 rounded-md p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">
                    All Extracted Match Links ({result.total_links})
                  </h3>
                  <div className="max-h-64 overflow-y-auto border border-gray-200 rounded bg-white">
                    {result.seasons.map((season, seasonIndex) => 
                      season.success && season.links.map((link, linkIndex) => (
                        <div key={`${seasonIndex}-${linkIndex}`} className="p-2 border-b border-gray-100 last:border-b-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {season.season_name}
                            </span>
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
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;