#!/usr/bin/env python3
"""
Debug the fixtures extraction to see what's happening
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_fixtures_page():
    print("🔍 DEBUGGING FIXTURES EXTRACTION")
    print("="*50)
    
    # Test with a season we know exists
    test_url = "https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"📡 Loading: {test_url}")
            await page.goto(test_url, timeout=60000)
            
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for tables
            all_tables = soup.find_all('table')
            print(f"📊 Found {len(all_tables)} tables")
            
            for i, table in enumerate(all_tables[:5]):
                table_id = table.get('id', f'no-id-{i}')
                rows = len(table.find_all('tr'))
                print(f"   Table {i+1}: ID='{table_id}', Rows={rows}")
                
                # Check for match links
                links = table.find_all('a', href=lambda x: x and '/matches/' in x)
                if links:
                    print(f"      Match links found: {len(links)}")
                    for j, link in enumerate(links[:3]):
                        href = link.get('href')
                        text = link.get_text().strip()
                        print(f"         {j+1}. {text} -> {href}")
            
            # Try to find any links with /matches/ 
            all_match_links = soup.find_all('a', href=lambda x: x and '/matches/' in x)
            print(f"\n🔗 Total match links on page: {len(all_match_links)}")
            
            if all_match_links:
                print("Sample match links:")
                for i, link in enumerate(all_match_links[:5]):
                    href = link.get('href')
                    text = link.get_text().strip()
                    print(f"   {i+1}. '{text}' -> {href}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_fixtures_page())