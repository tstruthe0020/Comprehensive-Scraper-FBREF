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

class FBrefRestoredAPITest(unittest.TestCase):
    """Test suite for the restored FBref football data scraping API"""
    
    def setUp(self):
        """Setup for tests"""
        self.api_url = API_URL
        logger.info(f"Using API URL: {self.api_url}")
        self.status_id = None
    
    def test_01_api_connectivity(self):
        """Test basic API connectivity"""
        logger.info("Testing API root endpoint...")
        response = requests.get(f"{self.api_url}/", verify=False)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        logger.info(f"API root response: {data}")
        
        # Test matches endpoint
        logger.info("Testing matches endpoint...")
        response = requests.get(f"{self.api_url}/matches", verify=False)
        self.assertEqual(response.status_code, 200)
        logger.info(f"Matches endpoint accessible")
        
        # Test seasons endpoint
        logger.info("Testing seasons endpoint...")
        response = requests.get(f"{self.api_url}/seasons", verify=False)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("seasons", data)
        logger.info(f"Seasons endpoint response: {data}")
        
        # Test teams endpoint
        logger.info("Testing teams endpoint...")
        response = requests.get(f"{self.api_url}/teams", verify=False)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("teams", data)
        logger.info(f"Teams endpoint response: {data}")
    
    def test_02_start_scraping(self):
        """Test starting a scraping job for a season"""
        logger.info("Testing season scraping initiation...")
        
        # Start scraping for 2023-24 season
        response = requests.post(f"{self.api_url}/scrape-season/2023-24", verify=False)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status_id", data)
        self.status_id = data["status_id"]
        logger.info(f"Started scraping with status_id: {self.status_id}")
        
        # Store status_id for subsequent tests
        with open("status_id.txt", "w") as f:
            f.write(self.status_id)
        
        # Wait a bit for scraping to start
        time.sleep(5)
        
        # Check initial status
        response = requests.get(f"{self.api_url}/scraping-status/{self.status_id}", verify=False)
        self.assertEqual(response.status_code, 200)
        status_data = response.json()
        self.assertEqual(status_data["status"], "running", "Scraping status should be 'running'")
        logger.info(f"Initial scraping status: {status_data}")
        
        # Check if fixtures extraction is working by verifying total_matches
        self.assertIn("total_matches", status_data, "Status should include total_matches")
        self.assertGreater(status_data["total_matches"], 0, "Should find at least some matches")
        logger.info(f"Found {status_data['total_matches']} matches to scrape")
        
        # Wait for a few matches to be scraped (max 60 seconds)
        max_wait = 60
        wait_interval = 5
        total_wait = 0
        matches_scraped = 0
        
        logger.info("Monitoring scraping progress (waiting for at least 2 matches)...")
        while total_wait < max_wait:
            response = requests.get(f"{self.api_url}/scraping-status/{self.status_id}", verify=False)
            status_data = response.json()
            matches_scraped = status_data["matches_scraped"]
            
            logger.info(f"Progress: {matches_scraped}/{status_data['total_matches']} matches scraped")
            
            # For testing purposes, we only need a few matches
            if matches_scraped >= 2:
                logger.info("Sufficient matches scraped for testing purposes")
                break
                
            time.sleep(wait_interval)
            total_wait += wait_interval
        
        # Verify that at least some matches were scraped
        self.assertGreater(matches_scraped, 0, "Should have scraped at least one match")
    
    def test_03_check_scraped_data(self):
        """Test retrieving and validating scraped match data"""
        logger.info("Testing scraped match data...")
        
        # Get status_id from file if not set
        if not self.status_id:
            try:
                with open("status_id.txt", "r") as f:
                    self.status_id = f.read().strip()
            except FileNotFoundError:
                self.fail("No status_id available from previous test")
        
        # Check if scraping is still in progress
        response = requests.get(f"{self.api_url}/scraping-status/{self.status_id}", verify=False)
        status_data = response.json()
        logger.info(f"Current scraping status: {status_data['status']}")
        
        # Get matches for the 2023-24 season
        response = requests.get(f"{self.api_url}/matches?season=2023-24", verify=False)
        self.assertEqual(response.status_code, 200)
        matches = response.json()
        
        # Verify we have some matches
        self.assertGreater(len(matches), 0, "Should have at least one match in the database")
        logger.info(f"Found {len(matches)} matches in the database")
        
        # Validate the structure of the first match
        if matches:
            match = matches[0]
            logger.info("Validating match data structure...")
            required_fields = [
                "id", "match_date", "home_team", "away_team", 
                "home_score", "away_score", "season", "match_url"
            ]
            
            for field in required_fields:
                self.assertIn(field, match, f"Match should have {field} field")
                logger.info(f"✓ {field}: {match.get(field)}")
            
            # Validate team stats
            team_stat_fields = [
                "home_possession", "home_shots", "home_shots_on_target",
                "away_possession", "away_shots", "away_shots_on_target"
            ]
            
            logger.info("Validating team statistics...")
            for field in team_stat_fields:
                self.assertIn(field, match, f"Match should have {field} field")
                logger.info(f"✓ {field}: {match.get(field)}")
            
            # Validate match URL format
            self.assertTrue(match["match_url"].startswith("https://fbref.com/en/matches/"), 
                           "Match URL should be from fbref.com")
            
            logger.info(f"Match between {match['home_team']} and {match['away_team']} validated successfully")
    
    def test_04_export_csv(self):
        """Test CSV export functionality"""
        logger.info("Testing CSV export...")
        
        # Create filter request for 2023-24 season
        filter_data = {
            "season": "2023-24",
            "teams": [],
            "referee": None
        }
        
        # Request CSV export
        response = requests.post(f"{self.api_url}/export-csv", json=filter_data, verify=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv", "Response should be CSV")
        
        # Check if we got CSV data
        csv_data = response.text
        self.assertGreater(len(csv_data), 0, "CSV data should not be empty")
        
        # Check if CSV has headers
        headers = csv_data.split("\n")[0]
        self.assertIn("home_team", headers, "CSV should have home_team column")
        self.assertIn("away_team", headers, "CSV should have away_team column")
        
        logger.info(f"CSV export successful, received {len(csv_data)} bytes")
        logger.info(f"CSV headers: {headers}")

def run_tests():
    """Run the test suite"""
    logger.info("Starting tests for restored FBref football data scraping API")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    run_tests()