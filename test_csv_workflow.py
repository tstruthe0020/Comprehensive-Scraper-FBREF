#!/usr/bin/env python3
"""
Test the CSV-based scraper workflow
"""

import asyncio
import sys
sys.path.append('/app/backend')

from csv_scraper import CSVMatchReportScraper

async def test_csv_workflow():
    """Test the CSV workflow with a small sample"""
    
    print("🔍 Testing CSV Workflow...")
    
    # Test URL that should have completed matches
    fixtures_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    
    scraper = CSVMatchReportScraper(rate_limit_delay=1, headless=True)
    
    try:
        print("Step 1: Setting up browser...")
        if not await scraper.setup_browser():
            print("❌ Browser setup failed")
            return
        
        print("Step 2: Extracting match URLs...")
        match_urls = await scraper.extract_match_urls_from_fixtures(fixtures_url)
        
        if not match_urls:
            print("❌ No match URLs found")
            return
        
        print(f"✅ Found {len(match_urls)} match URLs")
        print(f"Sample URL: {match_urls[0] if match_urls else 'None'}")
        
        # Test with just first 2 matches
        test_urls = match_urls[:2]
        
        print("Step 3: Creating initial CSV...")
        csv_content = scraper.create_initial_csv(test_urls)
        
        if not csv_content:
            print("❌ CSV creation failed")
            return
        
        print(f"✅ Initial CSV created ({len(csv_content)} characters)")
        
        # Test scraping one match
        if test_urls:
            print(f"Step 4: Testing match stats scraping for first match...")
            stats = await scraper.scrape_team_and_player_stats(test_urls[0])
            
            if stats:
                print(f"✅ Match stats extracted:")
                print(f"   - Match info: {bool(stats.get('match_info'))}")
                print(f"   - Team stats: {len(stats.get('team_stats', {}))}")
                print(f"   - Player stats: {len(stats.get('player_stats', []))}")
                
                print("Step 5: Testing CSV update...")
                updated_csv = scraper.update_csv_with_stats(csv_content, test_urls[0], stats)
                
                if updated_csv != csv_content:
                    print("✅ CSV successfully updated with stats")
                else:
                    print("⚠️ CSV update made no changes")
            else:
                print("❌ No match stats extracted")
        
        print("\n🎉 CSV Workflow Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_csv_workflow())