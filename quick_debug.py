#!/usr/bin/env python3
"""
Quick debug of why fixtures extraction is failing
"""

import asyncio
import sys
sys.path.append('/app/backend')

async def debug_fixtures_directly():
    from server import scraper
    
    print("🔍 DIRECT FIXTURES DEBUG")
    print("="*40)
    
    # Setup browser
    success = await scraper.setup_browser()
    if not success:
        print("❌ Browser setup failed")
        return
    
    print("✅ Browser setup successful")
    
    try:
        # Test fixtures extraction directly
        fixtures = await scraper.extract_season_fixtures("2023-24")
        print(f"📊 Fixtures found: {len(fixtures)}")
        
        if fixtures:
            for i, fixture in enumerate(fixtures[:3]):
                print(f"   {i+1}. {fixture.home_team} vs {fixture.away_team}")
                print(f"      URL: {fixture.match_url}")
        else:
            print("❌ No fixtures extracted")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_fixtures_directly())