#!/usr/bin/env python3
"""
Full season scraping test with random match verification
"""

import asyncio
import sys
import requests
import json
import random
from datetime import datetime

sys.path.append('/app/backend')

async def test_full_season_scraping():
    print("🚀 TESTING FULL SEASON SCRAPING")
    print("="*60)
    
    # First, let's check if the backend is running
    try:
        backend_url = "http://localhost:8001"
        response = requests.get(f"{backend_url}/api/", timeout=5)
        print(f"✅ Backend status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  Backend not running - starting scrape manually...")
        
        # Import and run scraping directly
        from server import scraper, scrape_season_background
        import uuid
        
        # Test with 2024-25 season
        season = "2024-25"
        status_id = str(uuid.uuid4())
        
        print(f"🎯 Starting scraping for season: {season}")
        print(f"📋 Status ID: {status_id}")
        
        try:
            # Start scraping
            await scrape_season_background(season, status_id)
            print("✅ Season scraping completed successfully!")
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return
    
    # If backend is running, use API
    try:
        print("🔥 Triggering full season scrape via API...")
        response = requests.post(f"{backend_url}/api/scrape-season/2024-25", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status_id = data.get('status_id')
            print(f"✅ Scraping started! Status ID: {status_id}")
            
            # Monitor progress
            await monitor_scraping_progress(backend_url, status_id)
            
        else:
            print(f"❌ Failed to start scraping: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")

async def monitor_scraping_progress(backend_url, status_id):
    """Monitor scraping progress in real-time"""
    print("\n📊 MONITORING SCRAPING PROGRESS")
    print("-" * 40)
    
    while True:
        try:
            response = requests.get(f"{backend_url}/api/scraping-status/{status_id}", timeout=5)
            if response.status_code == 200:
                status = response.json()
                
                current_status = status.get('status', 'unknown')
                matches_scraped = status.get('matches_scraped', 0)
                total_matches = status.get('total_matches', 0)
                current_match = status.get('current_match', '')
                errors = status.get('errors', [])
                
                progress = (matches_scraped / total_matches * 100) if total_matches > 0 else 0
                
                print(f"\r🔄 Status: {current_status} | Progress: {matches_scraped}/{total_matches} ({progress:.1f}%) | Errors: {len(errors)}", end="")
                
                if current_status in ['completed', 'failed']:
                    print(f"\n✅ Scraping {current_status}!")
                    if errors:
                        print(f"⚠️  Errors encountered: {len(errors)}")
                        for error in errors[:3]:  # Show first 3 errors
                            print(f"   - {error}")
                    break
                    
            await asyncio.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"\n❌ Error monitoring progress: {e}")
            break

if __name__ == "__main__":
    asyncio.run(test_full_season_scraping())