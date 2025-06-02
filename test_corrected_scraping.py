#!/usr/bin/env python3
"""
Test actual scraping with corrected URLs
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test_corrected_urls():
    """Test the corrected URL patterns with real scraping"""
    print("🚀 Testing Corrected URL Patterns with Real Scraping")
    
    playwright = None
    browser = None
    page = None
    
    # Test URLs based on our corrected logic
    test_urls = {
        "Current 2024-25": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
        "Historical 2023-24": "https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures",
        "Historical 2022-23": "https://fbref.com/en/comps/9/2022-2023/schedule/2022-2023-Premier-League-Scores-and-Fixtures"
    }
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for season_name, url in test_urls.items():
            print(f"\n🧪 Testing {season_name}")
            print(f"   🔗 URL: {url}")
            
            try:
                await page.goto(url, wait_until='networkidle')
                
                # Get page info
                title = await page.title()
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Count match links
                match_links = 0
                sample_links = []
                for link in soup.find_all('a'):
                    href = link.get('href', '')
                    if '/matches/' in href:
                        match_links += 1
                        if len(sample_links) < 3:
                            sample_links.append(f"https://fbref.com{href}")
                
                # Find schedule tables
                schedule_tables = []
                for table in soup.find_all('table'):
                    table_id = table.get('id', '')
                    if 'sched' in table_id.lower():
                        schedule_tables.append(table_id)
                
                print(f"   📄 Title: {title}")
                print(f"   📊 Schedule tables: {schedule_tables}")
                print(f"   🔗 Match links found: {match_links}")
                
                if match_links > 0:
                    print(f"   ✅ SUCCESS! Found {match_links} match links")
                    print(f"   🎯 Sample links:")
                    for sample_link in sample_links:
                        print(f"      - {sample_link}")
                else:
                    print(f"   ❌ FAILED: No match links found")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
        
        print("\n✅ URL testing completed")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        
    finally:
        if page:
            await page.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_corrected_urls())