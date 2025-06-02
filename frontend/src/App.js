import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FBrefScraper = () => {
  const [selectedSeason, setSelectedSeason] = useState("2024-25");
  const [scrapingStatus, setScrapingStatus] = useState(null);
  const [statusId, setStatusId] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [manualUrl, setManualUrl] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [availableSeasons, setAvailableSeasons] = useState(["2024-25", "2023-24", "2022-23", "2021-22"]);

  // Poll scraping status
  useEffect(() => {
    let interval;
    if (statusId && scrapingStatus?.status === "running") {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/scraping-status/${statusId}`);
          setScrapingStatus(response.data);
          
          if (response.data.status === "completed" || response.data.status === "failed") {
            clearInterval(interval);
            loadMatches();
          }
        } catch (error) {
          console.error("Error polling status:", error);
          clearInterval(interval);
        }
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [statusId, scrapingStatus?.status]);

  const loadMatches = async () => {
    try {
      const response = await axios.get(`${API}/matches?season=${selectedSeason}`);
      setMatches(response.data);
    } catch (error) {
      console.error("Error loading matches:", error);
    }
  };

  const startScraping = async (customUrl = null) => {
    try {
      setLoading(true);
      setErrorMessage("");
      
      let endpoint = `${API}/scrape-season/${selectedSeason}`;
      let requestData = {};
      
      if (customUrl) {
        // If we have a custom URL, we'll need to add a backend endpoint for this
        requestData = { custom_url: customUrl };
      }
      
      const response = await axios.post(endpoint, requestData);
      setStatusId(response.data.status_id);
      setScrapingStatus({ status: "running", matches_scraped: 0, total_matches: 0 });
      setShowUrlModal(false);
      setManualUrl("");
    } catch (error) {
      console.error("Error starting scraping:", error);
      setErrorMessage("Failed to start scraping. Please try again.");
      
      // Check if it's a URL not found error
      if (error.response?.data?.detail?.includes("No match URLs found")) {
        setShowUrlModal(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleManualUrlSubmit = () => {
    if (manualUrl.trim()) {
      startScraping(manualUrl.trim());
    }
  };

  const getProgressPercentage = () => {
    if (!scrapingStatus || !scrapingStatus.total_matches) return 0;
    return Math.round((scrapingStatus.matches_scraped / scrapingStatus.total_matches) * 100);
  };

  const formatStatusMessage = () => {
    if (!scrapingStatus) return "";
    
    if (scrapingStatus.status === "running") {
      return `Scraping in progress: ${scrapingStatus.matches_scraped}/${scrapingStatus.total_matches} matches`;
    } else if (scrapingStatus.status === "completed") {
      return `Scraping completed! ${scrapingStatus.matches_scraped} matches extracted`;
    } else if (scrapingStatus.status === "failed") {
      return `Scraping failed: ${scrapingStatus.errors?.join(", ") || "Unknown error"}`;
    }
    return "";
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">FBref Data Scraper</h1>
          <p className="text-gray-600">Extract Premier League match data from FBref.com</p>
        </div>

        {/* Main Control Panel */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Season Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Season
              </label>
              <select
                value={selectedSeason}
                onChange={(e) => setSelectedSeason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading || scrapingStatus?.status === "running"}
              >
                {availableSeasons.map(season => (
                  <option key={season} value={season}>{season}</option>
                ))}
              </select>
            </div>

            {/* Extract Button */}
            <div className="flex items-end">
              <button
                onClick={() => startScraping()}
                disabled={loading || scrapingStatus?.status === "running"}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? "Starting..." : scrapingStatus?.status === "running" ? "Scraping..." : `Extract ${selectedSeason} Data`}
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          {scrapingStatus && scrapingStatus.status === "running" && (
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{getProgressPercentage()}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${getProgressPercentage()}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Status Message */}
          {scrapingStatus && (
            <div className={`p-3 rounded-md ${
              scrapingStatus.status === "completed" ? "bg-green-100 text-green-800" :
              scrapingStatus.status === "failed" ? "bg-red-100 text-red-800" :
              "bg-blue-100 text-blue-800"
            }`}>
              {formatStatusMessage()}
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="mt-4 p-3 bg-red-100 text-red-800 rounded-md">
              {errorMessage}
            </div>
          )}
        </div>

        {/* Results Section */}
        {matches.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Extracted Matches ({matches.length})
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Match</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stadium</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {matches.slice(0, 10).map((match, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {match.match_date || "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {match.home_team} vs {match.away_team}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {match.home_score} - {match.away_score}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {match.stadium || "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {matches.length > 10 && (
                <p className="text-center text-gray-500 mt-4">
                  Showing first 10 of {matches.length} matches
                </p>
              )}
            </div>
          </div>
        )}

        {/* Manual URL Modal */}
        {showUrlModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Fixtures Page Not Found
              </h3>
              <p className="text-gray-600 mb-4">
                The automatic URL for {selectedSeason} season fixtures could not be found. 
                Please provide the correct FBref fixtures page URL:
              </p>
              <input
                type="url"
                value={manualUrl}
                onChange={(e) => setManualUrl(e.target.value)}
                placeholder="https://fbref.com/en/comps/9/..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              />
              <div className="flex space-x-3">
                <button
                  onClick={handleManualUrlSubmit}
                  disabled={!manualUrl.trim()}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400"
                >
                  Use This URL
                </button>
                <button
                  onClick={() => setShowUrlModal(false)}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<FBrefScraper />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
