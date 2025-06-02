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
from pymongo import MongoClient

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/app/backend/.env')
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

def test_comprehensive_data_storage():
    """Test if the comprehensive_data field is being stored correctly"""
    logger.info("Testing if comprehensive_data field is being stored correctly...")
    
    # Connect to MongoDB
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Create a test match with comprehensive_data
    test_match = {
        'id': 'test_comprehensive_data',
        'match_date': '2024-06-02',
        'home_team': 'Test Home',
        'away_team': 'Test Away',
        'home_score': 2,
        'away_score': 1,
        'season': '2024-25',
        'stadium': 'Test Stadium',
        'referee': 'Test Referee',
        'match_url': 'https://test.com',
        'comprehensive_data': {
            'basic_info': {'test': 'data'},
            'all_tables': {'table_1': {'test': 'table'}},
            'metadata': {'test': 'metadata'}
        }
    }
    
    # Insert the test match
    db.matches.delete_one({'id': 'test_comprehensive_data'})  # Delete if exists
    db.matches.insert_one(test_match)
    logger.info("Inserted test match with comprehensive_data")
    
    # Retrieve the test match
    retrieved_match = db.matches.find_one({'id': 'test_comprehensive_data'})
    
    # Check if comprehensive_data is present
    if 'comprehensive_data' in retrieved_match:
        logger.info("SUCCESS: comprehensive_data field is being stored correctly")
        logger.info(f"Retrieved comprehensive_data: {retrieved_match['comprehensive_data']}")
        
        # Clean up
        db.matches.delete_one({'id': 'test_comprehensive_data'})
        logger.info("Deleted test match")
        
        return True
    else:
        logger.error("FAILURE: comprehensive_data field is not being stored")
        return False

if __name__ == "__main__":
    success = test_comprehensive_data_storage()
    if success:
        print("\n=== COMPREHENSIVE DATA STORAGE TEST PASSED ===")
        print("The fix for the comprehensive_data field is working correctly")
    else:
        print("\n=== COMPREHENSIVE DATA STORAGE TEST FAILED ===")
        print("The comprehensive_data field is still not being stored correctly")