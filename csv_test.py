#!/usr/bin/env python3
"""
Test script for the CSV-based match report scraper endpoints
"""

import requests
import json
import base64
import csv
import io
import time
import os
from typing import Dict, Any

# Get backend URL from environment or use default
BACKEND_URL = "http://localhost:8001/api"

def test_csv_endpoints():
    """Test all CSV-based match report scraper endpoints"""
    print("\n===== Testing CSV-based Match Report Scraper Endpoints =====\n")
    
    # Test 1: Health Check
    test_health_check()
    
    # Test 2: CSV Extract URLs Only
    test_csv_extract_urls_only()
    
    # Test 3: Demo CSV Workflow
    test_demo_csv_workflow()
    
    # Test 4: Complete CSV Scrape Workflow
    test_csv_scrape_workflow()
    
    print("\n===== CSV-based Match Report Scraper Endpoints Testing Complete =====\n")

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    response = requests.get(f"{BACKEND_URL}/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, "Health check failed"
    assert response.json()["status"] == "healthy", "Health check returned unhealthy status"
    
    print("✅ Health check endpoint working correctly")
    return True

def test_csv_extract_urls_only():
    """Test the CSV extract URLs only endpoint"""
    print("\n=== Testing CSV Extract URLs Only Endpoint ===")
    
    # Test data
    test_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    payload = {
        "urls": [test_url],
        "max_matches": 5  # Limit to 5 matches for testing
    }
    
    # Make request
    response = requests.post(f"{BACKEND_URL}/csv-extract-urls-only", json=payload)
    
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200, "CSV extract URLs endpoint failed"
    
    data = response.json()
    print(f"Success: {data['success']}")
    print(f"Message: {data['message']}")
    print(f"Total Matches: {data['total_matches']}")
    
    assert data['success'] == True, "CSV extract URLs failed"
    assert data['total_matches'] > 0, "No match URLs found"
    assert data['csv_data'], "No CSV data returned"
    
    # Decode and check CSV content
    csv_content = base64.b64decode(data['csv_data']).decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    print(f"CSV rows: {len(rows)}")
    print(f"First row: {rows[0] if rows else 'No rows'}")
    
    assert len(rows) > 0, "CSV has no data rows"
    assert 'Match_URL' in rows[0], "CSV missing Match_URL column"
    assert 'Home_Team' in rows[0], "CSV missing Home_Team column"
    assert 'Away_Team' in rows[0], "CSV missing Away_Team column"
    
    print("✅ CSV extract URLs endpoint working correctly")
    return True

def test_demo_csv_workflow():
    """Test the demo CSV workflow endpoint"""
    print("\n=== Testing Demo CSV Workflow Endpoint ===")
    
    # Make request
    response = requests.post(f"{BACKEND_URL}/demo-csv-workflow")
    
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200, "Demo CSV workflow endpoint failed"
    
    data = response.json()
    print(f"Success: {data['success']}")
    print(f"Message: {data['message']}")
    print(f"Total Matches: {data['total_matches']}")
    print(f"Processed Matches: {data['processed_matches']}")
    
    assert data['success'] == True, "Demo CSV workflow failed"
    assert data['total_matches'] > 0, "No matches found"
    assert data['processed_matches'] > 0, "No matches processed"
    assert data['csv_data'], "No CSV data returned"
    
    # Decode and check CSV content
    csv_content = base64.b64decode(data['csv_data']).decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    print(f"CSV rows: {len(rows)}")
    
    # Check for team stats columns
    team_stat_columns = [
        'Home_Possession', 'Away_Possession',
        'Home_Shots_On_Target', 'Away_Shots_On_Target',
        'Home_Pass_Accuracy', 'Away_Pass_Accuracy',
        'Home_Saves', 'Away_Saves',
        'Home_Cards', 'Away_Cards'
    ]
    
    for column in team_stat_columns:
        assert column in rows[0], f"CSV missing {column} column"
    
    # Check that at least one row has been scraped
    scraped_rows = [row for row in rows if row.get('Scraped', '').strip().lower() == 'yes']
    print(f"Scraped rows: {len(scraped_rows)}")
    
    assert len(scraped_rows) > 0, "No rows were successfully scraped"
    
    # Check team stats for scraped rows
    for row in scraped_rows:
        print(f"Checking stats for match: {row.get('Home_Team', '')} vs {row.get('Away_Team', '')}")
        
        # Check that team stats were extracted
        assert row.get('Home_Possession', ''), "Home possession not extracted"
        assert row.get('Away_Possession', ''), "Away possession not extracted"
        
        # Print some stats for verification
        print(f"  Possession: {row.get('Home_Possession', '')}% - {row.get('Away_Possession', '')}%")
        print(f"  Shots on Target: {row.get('Home_Shots_On_Target', '')} - {row.get('Away_Shots_On_Target', '')}")
        print(f"  Pass Accuracy: {row.get('Home_Pass_Accuracy', '')}% - {row.get('Away_Pass_Accuracy', '')}%")
    
    print("✅ Demo CSV workflow endpoint working correctly")
    return True

def test_csv_scrape_workflow():
    """Test the complete CSV scrape workflow endpoint"""
    print("\n=== Testing Complete CSV Scrape Workflow Endpoint ===")
    
    # Test data
    test_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    payload = {
        "urls": [test_url],
        "max_matches": 3  # Limit to 3 matches for testing
    }
    
    # Make request
    response = requests.post(f"{BACKEND_URL}/csv-scrape-workflow", json=payload)
    
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200, "CSV scrape workflow endpoint failed"
    
    data = response.json()
    print(f"Success: {data['success']}")
    print(f"Message: {data['message']}")
    print(f"Total Matches: {data['total_matches']}")
    print(f"Processed Matches: {data['processed_matches']}")
    
    assert data['success'] == True, "CSV scrape workflow failed"
    assert data['total_matches'] > 0, "No matches found"
    assert data['processed_matches'] > 0, "No matches processed"
    assert data['csv_data'], "No CSV data returned"
    
    # Decode and check CSV content
    csv_content = base64.b64decode(data['csv_data']).decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)
    
    print(f"CSV rows: {len(rows)}")
    
    # Check for team stats columns
    team_stat_columns = [
        'Home_Possession', 'Away_Possession',
        'Home_Shots_On_Target', 'Away_Shots_On_Target',
        'Home_Pass_Accuracy', 'Away_Pass_Accuracy',
        'Home_Saves', 'Away_Saves',
        'Home_Cards', 'Away_Cards'
    ]
    
    for column in team_stat_columns:
        assert column in rows[0], f"CSV missing {column} column"
    
    # Check that at least one row has been scraped
    scraped_rows = [row for row in rows if row.get('Scraped', '').strip().lower() == 'yes']
    print(f"Scraped rows: {len(scraped_rows)}")
    
    assert len(scraped_rows) > 0, "No rows were successfully scraped"
    
    # Check team stats for scraped rows
    for row in scraped_rows:
        print(f"Checking stats for match: {row.get('Home_Team', '')} vs {row.get('Away_Team', '')}")
        
        # Check that team stats were extracted
        assert row.get('Home_Possession', ''), "Home possession not extracted"
        assert row.get('Away_Possession', ''), "Away possession not extracted"
        
        # Print some stats for verification
        print(f"  Possession: {row.get('Home_Possession', '')}% - {row.get('Away_Possession', '')}%")
        print(f"  Shots on Target: {row.get('Home_Shots_On_Target', '')} - {row.get('Away_Shots_On_Target', '')}")
        print(f"  Pass Accuracy: {row.get('Home_Pass_Accuracy', '')}% - {row.get('Away_Pass_Accuracy', '')}%")
    
    print("✅ Complete CSV scrape workflow endpoint working correctly")
    return True

if __name__ == "__main__":
    test_csv_endpoints()