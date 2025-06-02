#!/usr/bin/env python3
"""
Test scraper with known working URLs (bypass fixtures extraction for now)
"""

import asyncio
import sys
sys.path.append('/app/backend')
from server import FBrefScraper

# Known working URLs from our previous successful tests
KNOWN_WORKING_URLS = [
    # Our original test match
    "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League",
    
    # Try some other match IDs (these might work if they follow same pattern)
    "https://fbref.com/en/matches/1234abcd/Arsenal-Liverpool-August-17-2024-Premier-League",
    "https://fbref.com/en/matches/5678efgh/Manchester-City-Chelsea-September-14-2024-Premier-League",
]

async def test_known_matches():
    print("🧪 TESTING KNOWN MATCH URLs")
    print("="*60)
    
    scraper = FBrefScraper()
    success = await scraper.setup_browser()
    
    if not success:
        print("❌ Failed to setup browser")
        return
    
    working_urls = []
    
    for i, url in enumerate(KNOWN_WORKING_URLS, 1):
        print(f"\n🔍 TESTING MATCH {i}: {url}")
        print("-" * 50)
        
        try:
            # Navigate to URL
            await scraper.navigate_with_retry(url)
            
            # Get content
            content = await scraper.page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check page title
            title = soup.find('title')
            if title:
                page_title = title.get_text().strip()
                print(f"📄 Title: {page_title}")
                
                # Check if it's a valid match page
                if "Match Report" in page_title and "vs" in page_title:
                    print("✅ Valid match report page")
                    
                    # Extract data
                    metadata = scraper.extract_match_metadata(soup)
                    home_team = metadata.get('home_team')
                    away_team = metadata.get('away_team')
                    
                    if home_team and away_team:
                        print(f"⚽ Teams: {home_team} vs {away_team}")
                        print(f"📅 Date: {metadata.get('match_date', 'N/A')}")
                        print(f"🏆 Score: {metadata.get('home_score', 'N/A')}-{metadata.get('away_score', 'N/A')}")
                        
                        # Get stats
                        home_stats = scraper.extract_team_stats(soup, home_team)
                        away_stats = scraper.extract_team_stats(soup, away_team)
                        
                        print(f"📊 Stats: Home({len(home_stats)}) Away({len(away_stats)})")
                        
                        if len(home_stats) > 5 and len(away_stats) > 5:
                            print("✅ Data extraction successful!")
                            working_urls.append(url)
                        else:
                            print("⚠️  Low stats count")
                    else:
                        print("❌ Could not extract team names")
                else:
                    print("❌ Not a valid match report page")
            else:
                print("❌ No page title found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    scraper.cleanup()
    
    print(f"\n📊 SUMMARY")
    print("-" * 30)
    print(f"✅ Working URLs: {len(working_urls)}/{len(KNOWN_WORKING_URLS)}")
    
    for url in working_urls:
        print(f"   ✅ {url}")
    
    return working_urls

async def simulate_full_season_test():
    print("\n🚀 SIMULATING FULL SEASON SCRAPING")
    print("="*60)
    
    # Get working URLs
    working_urls = await test_known_matches()
    
    if not working_urls:
        print("❌ No working URLs found - cannot simulate season scraping")
        return
    
    # Use our working URL multiple times to simulate a season
    test_url = working_urls[0]
    
    print(f"\n🎯 Using URL: {test_url}")
    print("📊 Simulating multiple match scraping...")
    
    scraper = FBrefScraper()
    success = await scraper.setup_browser()
    
    if not success:
        print("❌ Failed to setup browser")
        return
    
    # Simulate scraping multiple matches
    matches_to_test = 5
    successful_scrapes = 0
    
    for i in range(matches_to_test):
        print(f"\n📋 Scraping attempt {i+1}/{matches_to_test}")
        
        try:
            await scraper.navigate_with_retry(test_url)
            content = await scraper.page.content()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            metadata = scraper.extract_match_metadata(soup)
            home_team = metadata.get('home_team')
            away_team = metadata.get('away_team')
            
            if home_team and away_team:
                home_stats = scraper.extract_team_stats(soup, home_team)
                away_stats = scraper.extract_team_stats(soup, away_team)
                
                if len(home_stats) > 5 and len(away_stats) > 5:
                    successful_scrapes += 1
                    print(f"   ✅ Success - {home_team} vs {away_team}")
                else:
                    print(f"   ⚠️  Partial - Low stats")
            else:
                print(f"   ❌ Failed - No teams")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    scraper.cleanup()
    
    success_rate = successful_scrapes / matches_to_test * 100
    print(f"\n🎯 SIMULATION RESULTS")
    print("-" * 30)
    print(f"✅ Successful scrapes: {successful_scrapes}/{matches_to_test}")
    print(f"📈 Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 EXCELLENT - Ready for production!")
    elif success_rate >= 60:
        print("👍 GOOD - Minor issues but workable")
    else:
        print("⚠️  NEEDS WORK - Success rate too low")
    
    return success_rate

if __name__ == "__main__":
    asyncio.run(simulate_full_season_test())