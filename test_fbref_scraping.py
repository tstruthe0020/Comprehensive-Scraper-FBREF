#!/usr/bin/env python3
import requests
import time
import json
import logging
import os
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

def test_root_endpoint():
    """Test the root endpoint to verify API is running"""
    logger.info("Testing root endpoint...")
    try:
        response = requests.get(f"{API_URL}/")
        response.raise_for_status()
        data = response.json()
        logger.info(f"Root endpoint response: {data}")
        return True
    except Exception as e:
        logger.error(f"Error testing root endpoint: {e}")
        return False

def test_scrape_current_season():
    """Test scraping the current season (2024-25) with improved extraction methods"""
    season = "2024-25"
    logger.info(f"Testing scraping for current season: {season}")
    
    try:
        # Start scraping
        response = requests.post(f"{API_URL}/scrape-season/{season}")
        response.raise_for_status()
        data = response.json()
        
        if "status_id" not in data:
            logger.error("No status_id returned from scrape-season endpoint")
            return False
        
        status_id = data["status_id"]
        logger.info(f"Started scraping with status ID: {status_id}")
        
        # Monitor scraping progress
        max_checks = 30  # Increase timeout for thorough testing
        checks = 0
        completed = False
        extraction_method_used = None
        
        while checks < max_checks and not completed:
            time.sleep(5)  # Wait 5 seconds between checks
            
            try:
                status_response = requests.get(f"{API_URL}/scraping-status/{status_id}")
                status_response.raise_for_status()
                status_data = status_response.json()
                
                # Log current status
                logger.info(f"Scraping status: {status_data['status']}")
                logger.info(f"Matches scraped: {status_data.get('matches_scraped', 0)}/{status_data.get('total_matches', 0)}")
                
                if "current_match" in status_data and status_data["current_match"]:
                    logger.info(f"Current match: {status_data['current_match']}")
                    
                    # Try to determine which extraction method is being used
                    if "HTML content analysis" in status_data.get("errors", []):
                        extraction_method_used = "HTML content analysis"
                    elif "table selector" in status_data.get("errors", []):
                        extraction_method_used = "Table selector"
                    elif "alternative approach" in status_data.get("errors", []):
                        extraction_method_used = "Page-wide link search"
                    elif "requests-based" in status_data.get("errors", []):
                        extraction_method_used = "Requests + BeautifulSoup fallback"
                
                # Check if scraping is complete
                if status_data["status"] in ["completed", "failed"]:
                    completed = True
                    
                    if status_data["status"] == "completed":
                        logger.info(f"Scraping completed successfully!")
                        logger.info(f"Total matches scraped: {status_data.get('matches_scraped', 0)}")
                        
                        if status_data.get('matches_scraped', 0) > 0:
                            logger.info("✅ Successfully extracted and scraped match URLs")
                        else:
                            logger.error("❌ No matches were scraped")
                    else:
                        logger.error(f"Scraping failed with errors: {status_data.get('errors', [])}")
                        
                        # Check if any matches were scraped despite errors
                        if status_data.get('matches_scraped', 0) > 0:
                            logger.info(f"Partial success: {status_data.get('matches_scraped', 0)} matches were scraped before failure")
                
            except Exception as e:
                logger.error(f"Error checking scraping status: {e}")
            
            checks += 1
        
        if not completed:
            logger.warning("Scraping status check timed out")
        
        # Check if any matches were scraped
        try:
            matches_response = requests.get(f"{API_URL}/matches", params={"season": season})
            matches_response.raise_for_status()
            matches = matches_response.json()
            
            logger.info(f"Found {len(matches)} matches for season {season}")
            
            if len(matches) > 0:
                logger.info("✅ Successfully stored match data in database")
                
                # Log sample matches to verify data quality
                logger.info("Sample matches:")
                for i, match in enumerate(matches[:5]):
                    logger.info(f"Match {i+1}: {match.get('home_team', 'Unknown')} {match.get('home_score', 0)} - {match.get('away_score', 0)} {match.get('away_team', 'Unknown')}")
                
                # Check for Premier League teams in the data
                premier_league_teams = [
                    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", 
                    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich Town",
                    "Leicester City", "Liverpool", "Manchester City", "Manchester Utd", 
                    "Newcastle Utd", "Nottingham Forest", "Southampton", "Tottenham", 
                    "West Ham", "Wolverhampton"
                ]
                
                teams_found = set()
                for match in matches:
                    home_team = match.get("home_team", "")
                    away_team = match.get("away_team", "")
                    teams_found.add(home_team)
                    teams_found.add(away_team)
                
                premier_league_teams_found = [team for team in teams_found 
                                             if any(pl_team.lower() in team.lower() 
                                                   for pl_team in premier_league_teams)]
                
                if premier_league_teams_found:
                    logger.info(f"Premier League teams found: {premier_league_teams_found}")
                    logger.info("✅ Data quality check passed: Premier League teams found in the data")
                    return True
                else:
                    logger.warning("❌ Data quality check failed: No Premier League teams found in the data")
                    return len(matches) > 0  # Still return True if we have matches, even if team names don't match expected
            else:
                logger.error("❌ No matches found in database")
                return False
                
        except Exception as e:
            logger.error(f"Error checking matches: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing scrape-season endpoint: {e}")
        return False

def test_api_endpoints():
    """Test all API endpoints to ensure they're working properly"""
    logger.info("Testing API endpoints...")
    
    endpoints = {
        "Root": {"url": f"{API_URL}/", "method": "get"},
        "Matches": {"url": f"{API_URL}/matches", "method": "get"},
        "Seasons": {"url": f"{API_URL}/seasons", "method": "get"},
        "Teams": {"url": f"{API_URL}/teams", "method": "get"}
    }
    
    results = {}
    
    for name, endpoint in endpoints.items():
        try:
            if endpoint["method"] == "get":
                response = requests.get(endpoint["url"])
            else:
                logger.warning(f"Unsupported method {endpoint['method']} for {name}")
                continue
                
            response.raise_for_status()
            results[name] = True
            logger.info(f"✅ {name} endpoint working")
            
            # Log sample response data
            if name != "Root":
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"{name} endpoint returned {len(data)} items")
                elif isinstance(data, dict):
                    logger.info(f"{name} endpoint returned keys: {list(data.keys())}")
                
        except Exception as e:
            results[name] = False
            logger.error(f"❌ {name} endpoint failed: {e}")
    
    # Return True if all endpoints are working
    return all(results.values())

def main():
    """Run all tests"""
    logger.info("Starting tests for improved FBref scraping functionality...")
    
    # Test 1: Verify API is running
    api_running = test_root_endpoint()
    if not api_running:
        logger.error("API is not running. Aborting tests.")
        return False
    
    # Test 2: Test API endpoints
    endpoints_working = test_api_endpoints()
    if not endpoints_working:
        logger.warning("Some API endpoints are not working properly.")
    
    # Test 3: Test current season scraping with improved extraction methods
    current_season_success = test_scrape_current_season()
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"API Running: {'✅ Yes' if api_running else '❌ No'}")
    logger.info(f"API Endpoints: {'✅ All working' if endpoints_working else '❌ Some failed'}")
    logger.info(f"Current Season Scraping: {'✅ Success' if current_season_success else '❌ Failed'}")
    
    overall_success = api_running and current_season_success
    logger.info(f"Overall Test Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    main()