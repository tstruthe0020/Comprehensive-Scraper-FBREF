#!/usr/bin/env python3
import requests
import time
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
import sys

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

class FBrefScraperTester:
    def __init__(self):
        self.api_url = API_URL
        
    def test_root_endpoint(self):
        """Test the root endpoint"""
        logger.info("Testing API root endpoint...")
        try:
            response = requests.get(f"{self.api_url}/")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.json()}")
            assert response.status_code == 200, "Root endpoint should return 200"
            return True
        except Exception as e:
            logger.error(f"Error testing root endpoint: {e}")
            return False
    
    def start_scraping_season(self, season):
        """Start scraping a season and return the status_id"""
        logger.info(f"Starting scraping for season {season}...")
        try:
            response = requests.post(f"{self.api_url}/scrape-season/{season}")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.json()}")
            assert response.status_code == 200, f"Failed to start scraping season {season}"
            return response.json().get("status_id")
        except Exception as e:
            logger.error(f"Error starting scraping: {e}")
            return None
    
    def monitor_scraping_status(self, status_id, max_wait_time=600, check_interval=10):
        """Monitor scraping status until completion or timeout"""
        logger.info(f"Monitoring scraping status {status_id}...")
        start_time = time.time()
        completed = False
        final_status = None
        
        try:
            while time.time() - start_time < max_wait_time:
                response = requests.get(f"{self.api_url}/scraping-status/{status_id}")
                if response.status_code != 200:
                    logger.error(f"Error getting status: {response.status_code}")
                    time.sleep(check_interval)
                    continue
                
                status_data = response.json()
                status = status_data.get("status")
                matches_scraped = status_data.get("matches_scraped", 0)
                total_matches = status_data.get("total_matches", 0)
                current_match = status_data.get("current_match", "")
                errors = status_data.get("errors", [])
                
                logger.info(f"Status: {status} | Progress: {matches_scraped}/{total_matches} | Current: {current_match}")
                if errors:
                    logger.warning(f"Errors: {errors}")
                
                if status == "completed" or status == "failed":
                    completed = True
                    final_status = status_data
                    break
                
                time.sleep(check_interval)
            
            if not completed:
                logger.warning(f"Monitoring timed out after {max_wait_time} seconds")
                # Get final status
                response = requests.get(f"{self.api_url}/scraping-status/{status_id}")
                if response.status_code == 200:
                    final_status = response.json()
            
            return final_status
        except Exception as e:
            logger.error(f"Error monitoring status: {e}")
            return None
    
    def verify_scraped_data(self, season=None, min_expected=10):
        """Verify that data was scraped correctly"""
        logger.info(f"Verifying scraped data for season {season}...")
        try:
            url = f"{self.api_url}/matches"
            if season:
                url += f"?season={season}"
            
            response = requests.get(url)
            assert response.status_code == 200, "Failed to get matches"
            
            matches = response.json()
            match_count = len(matches)
            logger.info(f"Found {match_count} matches for season {season}")
            
            if match_count < min_expected:
                logger.warning(f"Expected at least {min_expected} matches, but found only {match_count}")
            
            # Verify data quality for a sample of matches
            sample_size = min(5, match_count)
            if match_count > 0:
                logger.info(f"Data Quality Check (Sample of {sample_size} matches):")
                for i in range(sample_size):
                    match = matches[i]
                    logger.info(f"Match {i+1}:")
                    logger.info(f"  Date: {match.get('match_date')}")
                    logger.info(f"  Teams: {match.get('home_team')} vs {match.get('away_team')}")
                    logger.info(f"  Score: {match.get('home_score')} - {match.get('away_score')}")
                    logger.info(f"  Venue: {match.get('stadium')}")
                    logger.info(f"  Referee: {match.get('referee')}")
                    
                    # Check for real team names (not placeholders)
                    home_team = match.get('home_team', '')
                    away_team = match.get('away_team', '')
                    
                    if not home_team or home_team == "Home Team" or not away_team or away_team == "Away Team":
                        logger.warning("  Possible placeholder team names detected")
                    
                    # Check for stats
                    has_stats = (
                        match.get('home_possession', 0) > 0 or
                        match.get('away_possession', 0) > 0 or
                        match.get('home_shots', 0) > 0 or
                        match.get('away_shots', 0) > 0
                    )
                    
                    if not has_stats:
                        logger.warning("  No team statistics found")
            
            return {
                "match_count": match_count,
                "success": match_count >= min_expected,
                "matches": matches[:10]  # Return first 10 matches for detailed analysis
            }
        except Exception as e:
            logger.error(f"Error verifying data: {e}")
            return {"match_count": 0, "success": False, "error": str(e)}
    
    def test_current_season(self):
        """Test scraping the current season (2024-25)"""
        logger.info("========== TESTING CURRENT SEASON (2024-25) ==========")
        season = "2024-25"
        
        # Start scraping
        status_id = self.start_scraping_season(season)
        if not status_id:
            logger.error("Failed to start scraping current season")
            return False
        
        # Monitor status
        final_status = self.monitor_scraping_status(status_id)
        if not final_status:
            logger.error("Failed to monitor scraping status for current season")
            return False
        
        # Check if scraping was successful
        if final_status.get("status") != "completed":
            logger.error(f"Scraping failed: {json.dumps(final_status, indent=2)}")
            return False
        
        # Verify data
        verification = self.verify_scraped_data(season)
        return verification.get("success", False)
    
    def test_historical_season(self):
        """Test scraping a historical season (2023-24)"""
        logger.info("========== TESTING HISTORICAL SEASON (2023-24) ==========")
        season = "2023-24"
        
        # Start scraping
        status_id = self.start_scraping_season(season)
        if not status_id:
            logger.error("Failed to start scraping historical season")
            return False
        
        # Monitor status
        final_status = self.monitor_scraping_status(status_id)
        if not final_status:
            logger.error("Failed to monitor scraping status for historical season")
            return False
        
        # Check if scraping was successful
        if final_status.get("status") != "completed":
            logger.error(f"Scraping failed: {json.dumps(final_status, indent=2)}")
            return False
        
        # Verify data
        verification = self.verify_scraped_data(season)
        return verification.get("success", False)
    
    def verify_data_quality(self):
        """Verify the quality of scraped data across all seasons"""
        logger.info("========== VERIFYING DATA QUALITY ==========")
        
        # Get all matches
        try:
            response = requests.get(f"{self.api_url}/matches")
            assert response.status_code == 200, "Failed to get matches"
            
            matches = response.json()
            match_count = len(matches)
            logger.info(f"Found {match_count} total matches in database")
            
            if match_count == 0:
                logger.error("No matches found in database")
                return False
            
            # Get available seasons
            seasons_response = requests.get(f"{self.api_url}/seasons")
            if seasons_response.status_code == 200:
                seasons = seasons_response.json().get("seasons", [])
                logger.info(f"Available seasons: {seasons}")
            else:
                logger.warning("Could not get available seasons")
                seasons = []
            
            # Get available teams
            teams_response = requests.get(f"{self.api_url}/teams")
            if teams_response.status_code == 200:
                teams = teams_response.json().get("teams", [])
                logger.info(f"Available teams: {teams}")
                
                # Check for real Premier League team names
                premier_league_teams = [
                    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", 
                    "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham", 
                    "Liverpool", "Luton Town", "Manchester City", "Manchester United", 
                    "Newcastle United", "Nottingham Forest", "Sheffield United", 
                    "Tottenham", "West Ham", "Wolverhampton"
                ]
                
                real_teams_found = [team for team in teams if any(pl_team.lower() in team.lower() for pl_team in premier_league_teams)]
                logger.info(f"Found {len(real_teams_found)} real Premier League teams: {real_teams_found}")
                
                if len(real_teams_found) < 5:  # At least 5 real teams should be found
                    logger.warning("Few real Premier League teams found in data")
            else:
                logger.warning("Could not get available teams")
            
            # Analyze a sample of matches for data quality
            sample_size = min(10, match_count)
            logger.info(f"Analyzing data quality for {sample_size} sample matches:")
            
            quality_issues = 0
            for i in range(sample_size):
                match = matches[i]
                
                # Check for complete match data
                required_fields = ['match_date', 'home_team', 'away_team', 'home_score', 'away_score', 'season', 'stadium', 'referee']
                missing_fields = [field for field in required_fields if not match.get(field)]
                
                if missing_fields:
                    logger.warning(f"Match {i+1} is missing required fields: {missing_fields}")
                    quality_issues += 1
                
                # Check for real team names
                home_team = match.get('home_team', '')
                away_team = match.get('away_team', '')
                
                if not home_team or home_team == "Home Team" or not away_team or away_team == "Away Team":
                    logger.warning(f"Match {i+1} has placeholder team names: {home_team} vs {away_team}")
                    quality_issues += 1
                
                # Check for stats
                has_stats = (
                    match.get('home_possession', 0) > 0 or
                    match.get('away_possession', 0) > 0 or
                    match.get('home_shots', 0) > 0 or
                    match.get('away_shots', 0) > 0
                )
                
                if not has_stats:
                    logger.warning(f"Match {i+1} has no team statistics")
                    quality_issues += 1
                
                logger.info(f"Match {i+1}: {match.get('home_team')} {match.get('home_score')} - {match.get('away_score')} {match.get('away_team')} | Date: {match.get('match_date')} | Venue: {match.get('stadium')} | Referee: {match.get('referee')}")
            
            # Overall quality assessment
            if quality_issues == 0:
                logger.info("Data quality check passed: All sample matches have complete data")
                return True
            elif quality_issues < sample_size / 2:
                logger.warning(f"Data quality check partially passed: {quality_issues}/{sample_size} matches have issues")
                return True  # Still consider it a pass if less than half have issues
            else:
                logger.error(f"Data quality check failed: {quality_issues}/{sample_size} matches have issues")
                return False
            
        except Exception as e:
            logger.error(f"Error verifying data quality: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        results = {
            "root_endpoint": self.test_root_endpoint(),
            "current_season": None,
            "historical_season": None,
            "data_quality": None
        }
        
        # Test current season first (priority)
        results["current_season"] = self.test_current_season()
        
        # Test historical season
        results["historical_season"] = self.test_historical_season()
        
        # Verify data quality
        results["data_quality"] = self.verify_data_quality()
        
        # Print summary
        logger.info("========== TEST RESULTS SUMMARY ==========")
        for test, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test}: {status}")
        
        return results

if __name__ == "__main__":
    tester = FBrefScraperTester()
    
    # Check if specific test is requested
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "current":
            tester.test_current_season()
        elif test_name == "historical":
            tester.test_historical_season()
        elif test_name == "quality":
            tester.verify_data_quality()
        elif test_name == "root":
            tester.test_root_endpoint()
        else:
            logger.error(f"Unknown test: {test_name}")
    else:
        # Run all tests
        tester.run_all_tests()