#!/usr/bin/env python3
"""
Final targeted test to fix fixtures extraction
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test_and_fix_fixtures():
    print("🔧 FINAL FIXTURES EXTRACTION FIX")
    print("="*50)
    
    test_url = "https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"📡 Loading: {test_url}")
        await page.goto(test_url, timeout=60000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the correct table
        print(f"\n🔍 Looking for fixtures table...")
        all_tables = soup.find_all('table')
        
        target_table = None
        for table in all_tables:
            table_id = table.get('id', '')
            if 'sched' in table_id and '2023-2024' in table_id:
                target_table = table
                print(f"✅ Found target table: {table_id}")
                break
        
        if not target_table:
            print("❌ No sched table found")
            await browser.close()
            return
        
        # Analyze table structure
        rows = target_table.find_all('tr')
        print(f"📊 Table has {len(rows)} rows")
        
        # Look for Premier League matches
        premier_league_matches = []
        
        for i, row in enumerate(rows[1:10]):  # Check first 10 data rows
            cells = row.find_all(['td', 'th'])
            
            # Look for match links
            for cell in cells:
                links = cell.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    if '/matches/' in href:
                        full_url = f"https://fbref.com{href}"
                        link_text = link.get_text().strip()
                        
                        # Check if it's Premier League
                        if 'Premier-League' in href:
                            premier_league_matches.append({
                                'url': full_url,
                                'text': link_text,
                                'row_index': i
                            })
                            print(f"✅ Found PL match: {link_text} -> {full_url}")
        
        print(f"\n📊 RESULTS:")
        print(f"Total Premier League matches found: {len(premier_league_matches)}")
        
        if premier_league_matches:
            print(f"✅ SUCCESS - Can extract Premier League fixtures!")
            print(f"Sample matches:")
            for match in premier_league_matches[:5]:
                print(f"   {match['text']}")
        else:
            print(f"❌ NO Premier League matches found in table")
            
            # Debug: Show what links we did find
            print(f"\nDEBUG - Other match links found:")
            for row in rows[1:5]:
                for cell in row.find_all(['td', 'th']):
                    for link in cell.find_all('a'):
                        href = link.get('href', '')
                        if '/matches/' in href:
                            print(f"   {link.get_text().strip()} -> {href}")
        
        await browser.close()
        return len(premier_league_matches) > 0

if __name__ == "__main__":
    asyncio.run(test_and_fix_fixtures())