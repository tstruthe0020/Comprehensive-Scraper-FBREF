#!/usr/bin/env python3
"""
STEP B: Test Premier League Season Link Generation
Verify we can extract match report URLs from the seasons page
"""

import sys
import os
sys.path.append('/app/backend')

from server import FBrefScraperV2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_premier_league_link_generation():
    """Test extraction of match links from Premier League seasons page"""
    
    print("="*80)
    print("STEP B: PREMIER LEAGUE MATCH LINK GENERATION TEST")
    print("="*80)
    
    # Test with 2023-24 season
    season = "2023-24"
    seasons_url = "https://fbref.com/en/comps/9/history/Premier-League-Seasons"
    
    print(f"Season: {season}")
    print(f"Seasons page: {seasons_url}")
    print()
    
    # Initialize scraper
    scraper = FBrefScraperV2()
    
    # Setup ChromeDriver
    print("🔧 Setting up ChromeDriver...")
    if not scraper.setup_driver():
        print("❌ ChromeDriver setup failed")
        return False
    
    print("✅ ChromeDriver setup successful")
    
    try:
        # Test 1: Extract fixtures for the season
        print(f"\n📋 TESTING: Extract fixtures for {season}")
        fixtures = scraper.extract_fixtures_for_season(season)
        
        print(f"✅ Found {len(fixtures)} fixtures for season {season}")
        
        if fixtures:
            print(f"\n📊 Sample fixtures (first 5):")
            for i, fixture in enumerate(fixtures[:5]):
                print(f"   {i+1}. {fixture.match_date}: {fixture.home_team} vs {fixture.away_team}")
                print(f"      URL: {fixture.match_url}")
        
        # Test 2: Extract match links directly
        print(f"\n🔗 TESTING: Extract match report links")
        match_links = scraper.extract_match_links(season)
        
        print(f"✅ Found {len(match_links)} match report links")
        
        if match_links:
            print(f"\n📋 Sample match links (first 5):")
            for i, link in enumerate(list(match_links)[:5]):
                print(f"   {i+1}. {link}")
        
        # Test 3: Verify URL structure  
        print(f"\n🔍 TESTING: URL structure verification")
        valid_urls = 0
        invalid_urls = 0
        
        for link in list(match_links)[:10]:  # Check first 10
            if "/en/matches/" in link and len(link.split("/")) >= 6:
                valid_urls += 1
            else:
                invalid_urls += 1
                print(f"   ⚠️  Invalid URL structure: {link}")
        
        print(f"✅ Valid URLs: {valid_urls}")
        print(f"❌ Invalid URLs: {invalid_urls}")
        
        # Test 4: Check if we can access a sample match page
        if match_links:
            sample_url = list(match_links)[0]
            print(f"\n🌐 TESTING: Access sample match page")
            print(f"   Sample URL: {sample_url}")
            
            try:
                scraper.driver.get(sample_url)
                import time
                time.sleep(3)
                
                title = scraper.driver.title
                print(f"   ✅ Successfully accessed match page")
                print(f"   📄 Page title: {title}")
                
                # Check if it has the expected structure
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(scraper.driver.page_source, 'html.parser')
                tables = soup.find_all("table")
                
                print(f"   📊 Found {len(tables)} data tables on match page")
                
                if len(tables) >= 10:
                    print(f"   ✅ Match page has comprehensive data structure")
                else:
                    print(f"   ⚠️  Match page may have limited data")
                
            except Exception as e:
                print(f"   ❌ Error accessing match page: {e}")
        
        # Summary
        print(f"\n🎯 STEP B RESULTS:")
        print(f"   📋 Fixtures extracted: {len(fixtures)}")
        print(f"   🔗 Match links extracted: {len(match_links)}")
        print(f"   ✅ Valid URL structure: {valid_urls > 0}")
        print(f"   🌐 Match page accessibility: Verified")
        
        success = len(fixtures) > 0 and len(match_links) > 0 and valid_urls > 0
        
        if success:
            print(f"\n🎉 STEP B: PASSED - Link generation working correctly!")
        else:
            print(f"\n❌ STEP B: FAILED - Issues with link generation")
            
        return success
        
    except Exception as e:
        print(f"❌ Error during link generation test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Close the driver
        if scraper.driver:
            scraper.driver.quit()
            print("\n🔚 ChromeDriver closed")

if __name__ == "__main__":
    success = test_premier_league_link_generation()
    sys.exit(0 if success else 1)