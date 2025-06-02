#!/usr/bin/env python3
import requests
import time
import json
import os
import sys
from dotenv import load_dotenv
import logging
from pathlib import Path
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

class ComprehensiveExtractionTest:
    """Test suite for the comprehensive extraction implementation"""
    
    def __init__(self):
        self.api_url = API_URL
        logger.info(f"Using API URL: {self.api_url}")
    
    def test_api_root(self):
        """Test API root endpoint"""
        logger.info("Testing API root endpoint...")
        response = requests.get(f"{self.api_url}/", verify=False)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API root response: {data}")
            return True
        else:
            logger.error(f"API root endpoint failed with status code: {response.status_code}")
            return False
    
    def test_comprehensive_extraction(self):
        """Test comprehensive data extraction"""
        logger.info("Testing comprehensive data extraction...")
        
        # Start scraping for 2024-25 season
        response = requests.post(f"{self.api_url}/scrape-season/2024-25")
        if response.status_code != 200:
            logger.error(f"Failed to start scraping: {response.status_code}")
            return False
        
        data = response.json()
        status_id = data["status_id"]
        logger.info(f"Started scraping with status ID: {status_id}")
        
        # Monitor scraping progress
        max_checks = 20
        checks = 0
        completed = False
        
        while checks < max_checks and not completed:
            time.sleep(5)  # Wait 5 seconds between checks
            status_response = requests.get(f"{self.api_url}/scraping-status/{status_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info(f"Scraping status: {status_data['status']}, Matches scraped: {status_data.get('matches_scraped', 0)}/{status_data.get('total_matches', 0)}")
                
                if status_data["status"] in ["completed", "failed"]:
                    completed = True
                    if status_data["status"] == "failed":
                        logger.error(f"Scraping failed with errors: {status_data.get('errors', [])}")
                        if status_data.get('matches_scraped', 0) > 0:
                            logger.info(f"However, {status_data.get('matches_scraped', 0)} matches were scraped successfully.")
                            # Continue with testing since we have some data
                        else:
                            return False
                    else:
                        logger.info(f"Scraping completed successfully. Scraped {status_data.get('matches_scraped', 0)} matches.")
            else:
                logger.error(f"Failed to get scraping status: {status_response.status_code}")
            
            checks += 1
        
        # Verify data was scraped and comprehensive_data is present
        matches_response = requests.get(f"{self.api_url}/matches")
        if matches_response.status_code != 200:
            logger.error(f"Failed to get matches: {matches_response.status_code}")
            return False
        
        matches = matches_response.json()
        if not matches:
            logger.error("No matches found in the database")
            return False
        
        logger.info(f"Found {len(matches)} matches in the database")
        
        # Check for comprehensive_data in the first match
        sample_match = matches[0]
        if 'comprehensive_data' not in sample_match:
            logger.error("comprehensive_data field not found in match data")
            return False
        
        logger.info("comprehensive_data field found in match data")
        
        # Analyze comprehensive_data structure
        comprehensive_data = sample_match['comprehensive_data']
        
        # Check for all_tables
        if 'all_tables' not in comprehensive_data:
            logger.error("all_tables not found in comprehensive_data")
            return False
        
        all_tables = comprehensive_data['all_tables']
        table_count = len(all_tables)
        logger.info(f"Found {table_count} tables in comprehensive_data")
        
        if table_count == 0:
            logger.warning("No tables found in comprehensive_data")
        
        # Check for basic_info
        if 'basic_info' not in comprehensive_data:
            logger.error("basic_info not found in comprehensive_data")
            return False
        
        basic_info = comprehensive_data['basic_info']
        logger.info(f"basic_info found with keys: {', '.join(basic_info.keys())}")
        
        # Check for metadata
        if 'metadata' not in comprehensive_data:
            logger.error("metadata not found in comprehensive_data")
            return False
        
        metadata = comprehensive_data['metadata']
        logger.info(f"Found metadata with {metadata.get('total_tables_found', 0)} tables and {metadata.get('total_data_points', 0)} data points")
        
        # Check data-stat mappings in tables
        data_stat_mappings_found = False
        for table_key, table_data in all_tables.items():
            if 'data_stat_mapping' in table_data and table_data['data_stat_mapping']:
                data_stat_mappings_found = True
                logger.info(f"Found data-stat mapping in table {table_key} with {len(table_data['data_stat_mapping'])} mappings")
                logger.info(f"Sample data-stat keys: {list(table_data['data_stat_mapping'].keys())[:5]}")
                break
        
        if not data_stat_mappings_found:
            logger.warning("No data-stat mappings found in any table")
        
        # Check if basic match info is still extracted
        if not sample_match.get('home_team') or not sample_match.get('away_team'):
            logger.error("Basic match info (teams) not extracted")
            return False
        
        logger.info(f"Basic match info extracted: {sample_match.get('home_team')} vs {sample_match.get('away_team')}, Score: {sample_match.get('home_score')}-{sample_match.get('away_score')}")
        
        # Overall test result
        logger.info("Comprehensive extraction test completed successfully")
        return True
    
    def test_data_quality(self):
        """Test data quality of extracted data"""
        logger.info("Testing data quality...")
        
        # Get matches
        matches_response = requests.get(f"{self.api_url}/matches")
        if matches_response.status_code != 200:
            logger.error(f"Failed to get matches: {matches_response.status_code}")
            return False
        
        matches = matches_response.json()
        if not matches:
            logger.error("No matches found in the database")
            return False
        
        # Sample a match for detailed analysis
        sample_match = matches[0]
        comprehensive_data = sample_match.get('comprehensive_data', {})
        
        # Check table metadata
        all_tables = comprehensive_data.get('all_tables', {})
        for table_key, table_data in all_tables.items():
            table_metadata = table_data.get('table_metadata', {})
            if table_metadata:
                logger.info(f"Table {table_key} metadata: ID='{table_metadata.get('id', 'N/A')}', Class='{table_metadata.get('class', 'N/A')}'")
            
            # Check headers
            headers = table_data.get('headers', [])
            if headers:
                logger.info(f"Table {table_key} has {len(headers)} headers")
                data_stat_headers = [h for h in headers if h.get('data_stat')]
                logger.info(f"Found {len(data_stat_headers)} headers with data-stat attributes")
            
            # Check rows
            rows = table_data.get('rows', [])
            if rows:
                logger.info(f"Table {table_key} has {len(rows)} rows")
                
                # Check data-stat values in first row
                if rows and 'data_stat_values' in rows[0]:
                    data_stat_values = rows[0]['data_stat_values']
                    logger.info(f"First row has {len(data_stat_values)} data-stat values")
                    if data_stat_values:
                        logger.info(f"Sample data-stat keys in first row: {list(data_stat_values.keys())[:5]}")
        
        # Check basic match info extraction
        basic_info = comprehensive_data.get('basic_info', {})
        scorebox_data = basic_info.get('scorebox_data', {})
        if scorebox_data:
            logger.info("Scorebox data found")
            elements = scorebox_data.get('all_elements', [])
            logger.info(f"Scorebox contains {len(elements)} elements")
        
        match_info_box = basic_info.get('match_info_box', {})
        if match_info_box:
            logger.info(f"Match info box found with {len(match_info_box)} sections")
        
        # Check if the extraction functions are working correctly
        if sample_match.get('home_team') and sample_match.get('away_team'):
            logger.info(f"Team extraction successful: {sample_match.get('home_team')} vs {sample_match.get('away_team')}")
        else:
            logger.warning("Team extraction may not be working correctly")
        
        if sample_match.get('home_score') is not None and sample_match.get('away_score') is not None:
            logger.info(f"Score extraction successful: {sample_match.get('home_score')}-{sample_match.get('away_score')}")
        else:
            logger.warning("Score extraction may not be working correctly")
        
        if sample_match.get('match_date'):
            logger.info(f"Date extraction successful: {sample_match.get('match_date')}")
        else:
            logger.warning("Date extraction may not be working correctly")
        
        if sample_match.get('stadium'):
            logger.info(f"Stadium extraction successful: {sample_match.get('stadium')}")
        else:
            logger.warning("Stadium extraction may not be working correctly")
        
        if sample_match.get('referee'):
            logger.info(f"Referee extraction successful: {sample_match.get('referee')}")
        else:
            logger.warning("Referee extraction may not be working correctly")
        
        # Overall data quality assessment
        logger.info("Data quality test completed")
        return True
    
    def run_all_tests(self):
        """Run all tests and return results"""
        results = {}
        
        logger.info("Starting comprehensive extraction tests...")
        
        # Test 1: API Root
        logger.info("\n=== Test 1: API Root ===")
        results["api_root"] = self.test_api_root()
        
        # Test 2: Comprehensive Extraction
        logger.info("\n=== Test 2: Comprehensive Extraction ===")
        results["comprehensive_extraction"] = self.test_comprehensive_extraction()
        
        # Test 3: Data Quality
        logger.info("\n=== Test 3: Data Quality ===")
        results["data_quality"] = self.test_data_quality()
        
        # Print summary
        logger.info("\n=== Test Results Summary ===")
        for test_name, result in results.items():
            logger.info(f"{test_name}: {'PASS' if result else 'FAIL'}")
        
        # Overall result
        overall_result = all(results.values())
        logger.info(f"\nOverall Result: {'PASS' if overall_result else 'FAIL'}")
        
        return overall_result

if __name__ == "__main__":
    test = ComprehensiveExtractionTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)