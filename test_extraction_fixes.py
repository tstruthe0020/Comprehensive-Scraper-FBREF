#!/usr/bin/env python3
"""
Test the updated data extraction logic with a real match report
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import sys
import os

# Add the backend directory to the Python path
sys.path.append('/app/backend')

# Import the scraper classes
from server import FBrefScraper

TEST_URL = "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League"

async def test_data_extraction():
    print("🧪 TESTING UPDATED DATA EXTRACTION LOGIC")
    print("="*60)
    
    async with async_playwright() as p:
        try:
            # Setup browser
            print("🚀 Setting up browser...")
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to test URL
            print(f"📡 Navigating to test match...")
            await page.goto(TEST_URL, timeout=60000)
            
            # Get page content
            print("📄 Getting page content...")
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Create scraper instance
            scraper = FBrefScraper()
            
            # Test metadata extraction
            print("\n📋 TESTING METADATA EXTRACTION")
            print("-" * 40)
            
            metadata = scraper.extract_match_metadata(soup)
            
            for key, value in metadata.items():
                print(f"✅ {key}: {value}")
            
            if metadata.get("home_team") and metadata.get("away_team"):
                print(f"\n🎯 Teams successfully extracted: {metadata['home_team']} vs {metadata['away_team']}")
            else:
                print("❌ Failed to extract team names")
                
            # Test team stats extraction
            print("\n📊 TESTING TEAM STATS EXTRACTION")
            print("-" * 40)
            
            if metadata.get("home_team"):
                print(f"Extracting stats for {metadata['home_team']}...")
                home_stats = scraper.extract_team_stats(soup, metadata["home_team"])
                print(f"Home team stats: {len(home_stats)} fields extracted")
                
                for key, value in home_stats.items():
                    print(f"  {key}: {value}")
            
            if metadata.get("away_team"):
                print(f"\nExtracting stats for {metadata['away_team']}...")
                away_stats = scraper.extract_team_stats(soup, metadata["away_team"])
                print(f"Away team stats: {len(away_stats)} fields extracted")
                
                for key, value in away_stats.items():
                    print(f"  {key}: {value}")
            
            print("\n" + "="*60)
            print("✅ DATA EXTRACTION TEST COMPLETE")
            
            # Summary
            success_count = 0
            if metadata.get("home_team") and metadata.get("away_team"):
                success_count += 1
                print("✅ Team names: WORKING")
            else:
                print("❌ Team names: FAILED")
                
            if metadata.get("home_score") is not None and metadata.get("away_score") is not None:
                success_count += 1
                print("✅ Scores: WORKING")
            else:
                print("❌ Scores: FAILED")
                
            if len(home_stats) > 0 or len(away_stats) > 0:
                success_count += 1
                print("✅ Team stats: WORKING")
            else:
                print("❌ Team stats: FAILED")
            
            print(f"\n🎯 Overall success: {success_count}/3 components working")
            
            await browser.close()
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(test_data_extraction())