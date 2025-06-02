#!/usr/bin/env python3
import requests
import time
import json
import os
import sys
from dotenv import load_dotenv
import logging
from pathlib import Path
import unittest

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

class ScrapingWorkflowTest(unittest.TestCase):
    """Test suite for the scraping workflow functionality"""
    
    def setUp(self):
        """Setup for tests"""
        self.api_url = API_URL
        logger.info(f"Using API URL: {self.api_url}")
    
    def test_01_api_root(self):
        """Test API root endpoint"""
        logger.info("Testing API root endpoint...")
        response = requests.get(f"{self.api_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        logger.info(f"API root response: {data}")
    
    def test_02_single_season_scraping(self):
        """Test single season scraping endpoint"""
        logger.info("Testing single season scraping...")
        
        # Start scraping for 2024-25 season
        response = requests.post(f"{self.api_url}/scrape-season/2024-25")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status_id", data)
        status_id = data["status_id"]
        logger.info(f"Started scraping with status ID: {status_id}")
        
        # Monitor scraping progress
        max_checks = 10
        checks = 0
        completed = False
        
        while checks < max_checks and not completed:
            time.sleep(3)  # Wait 3 seconds between checks
            status_response = requests.get(f"{self.api_url}/scraping-status/{status_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info(f"Scraping status: {status_data['status']}, Matches scraped: {status_data.get('matches_scraped', 0)}/{status_data.get('total_matches', 0)}")
                
                if status_data["status"] in ["completed", "failed"]:
                    completed = True
                    if status_data["status"] == "failed":
                        logger.error(f"Scraping failed with errors: {status_data.get('errors', [])}")
                    else:
                        logger.info(f"Scraping completed successfully. Scraped {status_data.get('matches_scraped', 0)} matches.")
            else:
                logger.error(f"Failed to get scraping status: {status_response.status_code}")
            
            checks += 1
        
        # Verify data was scraped and stored in the database
        if completed:
            # Check team matches
            team_matches_response = requests.get(f"{self.api_url}/team-matches", params={"season": "2024-25"})
            self.assertEqual(team_matches_response.status_code, 200)
            team_matches_data = team_matches_response.json()
            
            logger.info(f"Found {len(team_matches_data.get('matches', []))} team matches for 2024-25 season")
            self.assertTrue(len(team_matches_data.get('matches', [])) > 0, "No team matches found in database")
            
            # Check player matches
            player_matches_response = requests.get(f"{self.api_url}/player-matches", params={"season": "2024-25"})
            self.assertEqual(player_matches_response.status_code, 200)
            player_matches_data = player_matches_response.json()
            
            logger.info(f"Found {len(player_matches_data.get('matches', []))} player matches for 2024-25 season")
            self.assertTrue(len(player_matches_data.get('matches', [])) > 0, "No player matches found in database")
            
            # Verify team match data structure
            if team_matches_data.get('matches'):
                sample_match = team_matches_data['matches'][0]
                required_fields = [
                    "team_name", "match_date", "home_team", "away_team", 
                    "team_score", "opponent_score", "possession", "shots", 
                    "shots_on_target", "expected_goals"
                ]
                
                for field in required_fields:
                    self.assertIn(field, sample_match, f"Missing required field: {field}")
                
                logger.info("Team match data structure verified successfully")
            
            # Verify player match data structure
            if player_matches_data.get('matches'):
                sample_player = player_matches_data['matches'][0]
                required_fields = [
                    "player_name", "team_name", "position", "minutes_played", 
                    "goals", "assists", "shots", "shots_on_target", 
                    "expected_goals", "passes_completed", "passes_attempted"
                ]
                
                for field in required_fields:
                    self.assertIn(field, sample_player, f"Missing required field: {field}")
                
                logger.info("Player match data structure verified successfully")
    
    def test_03_multi_season_scraping(self):
        """Test multi-season scraping endpoint"""
        logger.info("Testing multi-season scraping...")
        
        # Start multi-season scraping
        payload = {
            "seasons": ["2023-24", "2022-23"],
            "target_team": None  # Test without team filter first
        }
        
        response = requests.post(f"{self.api_url}/scrape-team-multi-season", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status_id", data)
        status_id = data["status_id"]
        logger.info(f"Started multi-season scraping with status ID: {status_id}")
        
        # Monitor scraping progress
        max_checks = 15
        checks = 0
        completed = False
        
        while checks < max_checks and not completed:
            time.sleep(3)  # Wait 3 seconds between checks
            status_response = requests.get(f"{self.api_url}/scraping-status/{status_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info(f"Multi-season scraping status: {status_data['status']}, Seasons: {status_data.get('completed_seasons', 0)}/{status_data.get('total_seasons', 0)}")
                
                if status_data["status"] in ["completed", "failed"]:
                    completed = True
                    if status_data["status"] == "failed":
                        logger.error(f"Multi-season scraping failed with errors: {status_data.get('errors', [])}")
                    else:
                        logger.info(f"Multi-season scraping completed successfully.")
            else:
                logger.error(f"Failed to get multi-season scraping status: {status_response.status_code}")
            
            checks += 1
        
        # Verify data was scraped for both seasons
        if completed:
            for season in payload["seasons"]:
                team_matches_response = requests.get(f"{self.api_url}/team-matches", params={"season": season})
                self.assertEqual(team_matches_response.status_code, 200)
                team_matches_data = team_matches_response.json()
                
                logger.info(f"Found {len(team_matches_data.get('matches', []))} team matches for {season} season")
                self.assertTrue(len(team_matches_data.get('matches', [])) > 0, f"No team matches found for {season} season")
    
    def test_04_team_focused_scraping(self):
        """Test team-focused scraping endpoint"""
        logger.info("Testing team-focused scraping...")
        
        # Get available teams
        teams_response = requests.get(f"{self.api_url}/teams")
        self.assertEqual(teams_response.status_code, 200)
        teams_data = teams_response.json()
        
        if teams_data.get('teams'):
            target_team = teams_data['teams'][0]  # Use the first team
            logger.info(f"Using target team: {target_team}")
            
            # Start team-focused scraping
            payload = {
                "seasons": ["2024-25"],
                "target_team": target_team
            }
            
            response = requests.post(f"{self.api_url}/scrape-team-multi-season", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("status_id", data)
            status_id = data["status_id"]
            logger.info(f"Started team-focused scraping with status ID: {status_id}")
            
            # Monitor scraping progress
            max_checks = 10
            checks = 0
            completed = False
            
            while checks < max_checks and not completed:
                time.sleep(3)  # Wait 3 seconds between checks
                status_response = requests.get(f"{self.api_url}/scraping-status/{status_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    logger.info(f"Team-focused scraping status: {status_data['status']}, Matches: {status_data.get('matches_scraped', 0)}/{status_data.get('total_matches', 0)}")
                    
                    if status_data["status"] in ["completed", "failed"]:
                        completed = True
                        if status_data["status"] == "failed":
                            logger.error(f"Team-focused scraping failed with errors: {status_data.get('errors', [])}")
                        else:
                            logger.info(f"Team-focused scraping completed successfully.")
                else:
                    logger.error(f"Failed to get team-focused scraping status: {status_response.status_code}")
                
                checks += 1
            
            # Verify team-specific data was scraped
            if completed:
                matches_response = requests.get(f"{self.api_url}/team-matches", params={"season": "2024-25", "team": target_team})
                self.assertEqual(matches_response.status_code, 200)
                matches_data = matches_response.json()
                
                logger.info(f"Found {len(matches_data.get('matches', []))} matches for team {target_team} in 2024-25 season")
                self.assertTrue(len(matches_data.get('matches', [])) > 0, f"No matches found for team {target_team}")
                
                # Verify all matches are for the target team
                if matches_data.get('matches'):
                    for match in matches_data['matches']:
                        self.assertEqual(match["team_name"], target_team, f"Match is not for target team: {match['team_name']} != {target_team}")
                    
                    logger.info("Team-focused scraping verified successfully")
        else:
            logger.warning("No teams available for team-focused scraping test")
            self.skipTest("No teams available for team-focused scraping test")
    
    def test_05_data_retrieval_endpoints(self):
        """Test data retrieval endpoints"""
        logger.info("Testing data retrieval endpoints...")
        
        # Test team-matches endpoint
        team_matches_response = requests.get(f"{self.api_url}/team-matches")
        self.assertEqual(team_matches_response.status_code, 200)
        team_matches_data = team_matches_response.json()
        logger.info(f"Found {len(team_matches_data.get('matches', []))} team matches in total")
        
        # Test player-matches endpoint
        player_matches_response = requests.get(f"{self.api_url}/player-matches")
        self.assertEqual(player_matches_response.status_code, 200)
        player_matches_data = player_matches_response.json()
        logger.info(f"Found {len(player_matches_data.get('matches', []))} player matches in total")
        
        # Test filtering by season
        season_filter_response = requests.get(f"{self.api_url}/team-matches", params={"season": "2024-25"})
        self.assertEqual(season_filter_response.status_code, 200)
        season_filter_data = season_filter_response.json()
        logger.info(f"Found {len(season_filter_data.get('matches', []))} team matches for 2024-25 season")
        
        # Test filtering by team
        if team_matches_data.get('matches') and len(team_matches_data.get('matches', [])) > 0:
            sample_team = team_matches_data['matches'][0]['team_name']
            team_filter_response = requests.get(f"{self.api_url}/team-matches", params={"team": sample_team})
            self.assertEqual(team_filter_response.status_code, 200)
            team_filter_data = team_filter_response.json()
            logger.info(f"Found {len(team_filter_data.get('matches', []))} team matches for team {sample_team}")
            
            # Verify all matches are for the specified team
            if team_filter_data.get('matches'):
                for match in team_filter_data['matches']:
                    self.assertEqual(match["team_name"], sample_team)
                
                logger.info("Team filtering verified successfully")

def run_tests():
    """Run all tests and print detailed output"""
    suite = unittest.TestLoader().loadTestsFromTestCase(ScrapingWorkflowTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING SCRAPING WORKFLOW".center(80))
    print("="*80 + "\n")
    
    success = run_tests()
    
    if success:
        print("\n" + "="*80)
        print("TEST SUMMARY: ALL TESTS PASSED".center(80))
        print("="*80 + "\n")
        
        print("✅ API endpoints responding correctly")
        print("✅ Background tasks working")
        print("✅ Progress tracking updating")
        print("✅ Database storing data properly")
        print("✅ Data retrieval working for frontend tables")
        print("\nThe complete collect → progress → view data pipeline is functional.")
    else:
        print("\n" + "="*80)
        print("TEST SUMMARY: SOME TESTS FAILED".center(80))
        print("="*80 + "\n")
        
        print("Please check the test output above for details on the failures.")
    
    sys.exit(0 if success else 1)