#!/usr/bin/env python3
"""
Test script to find correct historical season URL pattern
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test_historical_season_urls():
    """Test different URL patterns for historical seasons"""
    print("🔍 Testing historical season URL patterns...")
    
    playwright = None
    browser = None
    page = None
    
    # Different URL patterns to test for 2023-24 season
    test_urls = [
        "https://fbref.com/en/comps/9/2023-24/schedule/Premier-League-Scores-and-Fixtures",
        "https://fbref.com/en/comps/9/2023-24/schedule/2023-24-Premier-League-Scores-and-Fixtures", 
        "https://fbref.com/en/comps/9/2023-24/schedule/Premier-League-Scores-and-Fixtures-2023-24",
        "https://fbref.com/en/comps/9/2023-24/fixtures/Premier-League-Scores-and-Fixtures",
        "https://fbref.com/en/comps/9/2023-24/matches/Premier-League-Scores-and-Fixtures",
        "https://fbref.com/en/comps/9/2023-24/Premier-League-Scores-and-Fixtures"
    ]
    
    try:
        # Setup Playwright
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for i, test_url in enumerate(test_urls):
            print(f"\n🧪 Test {i+1}: {test_url}")
            
            try:
                # Navigate to page
                await page.goto(test_url, wait_until='networkidle')
                
                # Get page title
                title = await page.title()
                print(f"   📄 Title: {title}")
                
                # Check if this looks like a fixtures page vs stats page
                if "Scores & Fixtures" in title:
                    print("   ✅ LOOKS LIKE FIXTURES PAGE!")
                elif "Stats" in title:
                    print("   ❌ Stats page (not fixtures)")
                else:
                    print(f"   ❓ Unknown page type")
                
                # Get page content and check for match links
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Count match links
                match_links = 0
                for link in soup.find_all('a'):
                    href = link.get('href', '')
                    if '/matches/' in href:
                        match_links += 1
                
                print(f"   🔗 Match links found: {match_links}")
                
                # Check for schedule table
                tables = soup.find_all('table')
                schedule_tables = 0
                for table in tables:
                    table_id = table.get('id', '')
                    if 'sched' in table_id.lower():
                        schedule_tables += 1
                        print(f"   📊 Schedule table found: {table_id}")
                
                if match_links > 0:
                    print(f"   🎯 WORKING URL! Found {match_links} match links")
                
            except Exception as e:
                print(f"   ❌ Failed to load: {e}")
        
        print("\n✅ Historical URL testing completed")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        
    finally:
        # Cleanup
        if page:
            await page.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_historical_season_urls())