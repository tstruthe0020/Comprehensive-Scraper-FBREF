#!/usr/bin/env python3
import requests
import time
import json
import os
from typing import Dict, Any, List, Optional
import unittest
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from frontend .env file to get the backend URL
frontend_env_path = Path(__file__).parent / "frontend" / ".env"
if frontend_env_path.exists():
    load_dotenv(frontend_env_path)
    BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
else:
    BACKEND_URL = "http://localhost:8001"

API_URL = f"{BACKEND_URL}/api"
logger.info(f"Using API URL: {API_URL}")

def test_direct_match_url():
    """Test the API by directly providing a match URL"""
    logger.info("Testing direct match URL approach...")
    
    # Create a test match data
    test_match = {
        "match_url": "https://fbref.com/en/matches/3a6836b4/Burnley-Manchester-City-August-11-2023-Premier-League",
        "home_team": "Burnley",
        "away_team": "Manchester City",
        "home_score": 0,
        "away_score": 3,
        "match_date": "2023-08-11",
        "season": "2023-24",
        "stadium": "Turf Moor",
        "referee": "Craig Pawson"
    }
    
    # Insert the test match directly into the database
    logger.info("Inserting test match data directly into the database...")
    
    # Use the MongoDB connection from the backend
    from pymongo import MongoClient
    
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # Insert the test match
    result = db.matches.insert_one(test_match)
    logger.info(f"Inserted test match with ID: {result.inserted_id}")
    
    # Test the matches endpoint
    logger.info("Testing matches endpoint...")
    response = requests.get(f"{API_URL}/matches", verify=False)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    matches = response.json()
    logger.info(f"Found {len(matches)} matches")
    
    # Verify the test match is in the response
    found = False
    for match in matches:
        if match.get("match_url") == test_match["match_url"]:
            found = True
            logger.info("Found test match in the response!")
            logger.info(f"Match data: {match}")
            break
    
    assert found, "Test match not found in the response"
    
    # Test the seasons endpoint
    logger.info("Testing seasons endpoint...")
    response = requests.get(f"{API_URL}/seasons", verify=False)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    seasons = response.json()
    logger.info(f"Seasons: {seasons}")
    
    # Test the teams endpoint
    logger.info("Testing teams endpoint...")
    response = requests.get(f"{API_URL}/teams", verify=False)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    teams = response.json()
    logger.info(f"Teams: {teams}")
    
    # Test the CSV export
    logger.info("Testing CSV export...")
    filter_data = {
        "season": "2023-24",
        "teams": [],
        "referee": None
    }
    
    response = requests.post(f"{API_URL}/export-csv", json=filter_data, verify=False)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.headers["Content-Type"] == "text/csv", "Response should be CSV"
    
    csv_data = response.text
    assert len(csv_data) > 0, "CSV data should not be empty"
    
    logger.info(f"CSV export successful, received {len(csv_data)} bytes")
    
    # Clean up - remove the test match
    db.matches.delete_one({"match_url": test_match["match_url"]})
    logger.info("Test match removed from database")
    
    logger.info("All tests passed!")

if __name__ == "__main__":
    test_direct_match_url()