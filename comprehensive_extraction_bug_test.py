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

def test_comprehensive_extraction_bug():
    """Test to identify the bug in comprehensive data extraction"""
    logger.info("Testing comprehensive data extraction bug...")
    
    # Check the server.py file for the bug
    from pathlib import Path
    server_path = Path(__file__).parent / "backend" / "server.py"
    
    with open(server_path, 'r') as f:
        server_code = f.read()
    
    # Check for the bug in the code
    if "await db.matches.insert_one(match_data.dict())" in server_code:
        logger.error("BUG FOUND: match_data.dict() is being called on a dictionary")
        logger.info("The scrape_match_report function returns a dictionary, not a Pydantic model")
        logger.info("This is causing the comprehensive_data field to be lost")
        
        # Suggest the fix
        logger.info("FIX: Change 'await db.matches.insert_one(match_data.dict())' to 'await db.matches.insert_one(match_data)'")
        return True
    else:
        logger.info("No bug found in the code")
        return False

if __name__ == "__main__":
    bug_found = test_comprehensive_extraction_bug()
    if bug_found:
        print("\n=== COMPREHENSIVE EXTRACTION BUG FOUND ===")
        print("The comprehensive_data field is being lost because match_data.dict() is being called on a dictionary")
        print("FIX: Change 'await db.matches.insert_one(match_data.dict())' to 'await db.matches.insert_one(match_data)'")
    else:
        print("\n=== NO BUG FOUND ===")