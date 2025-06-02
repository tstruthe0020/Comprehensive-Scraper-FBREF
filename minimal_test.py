#!/usr/bin/env python3
"""
Minimal test to see exactly what's on the fixtures page
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def minimal_test():
    print("🔍 MINIMAL FIXTURES TEST")
    print("="*40)
    
    url = "https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"📡 Navigating to: {url}")
        await page.goto(url, timeout=60000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        title = soup.find('title')
        print(f"📄 Title: {title.get_text() if title else 'No title'}")
        
        # Find tables
        tables = soup.find_all('table')
        print(f"📊 Tables found: {len(tables)}")
        
        # Look for the specific table we need
        target_table = None
        for table in tables:
            table_id = table.get('id', '')
            if 'sched' in table_id and '2023-2024' in table_id:
                target_table = table
                print(f"✅ Found sched table: {table_id}")
                break
        
        if target_table:
            rows = target_table.find_all('tr')
            print(f"📊 Table rows: {len(rows)}")
            
            # Look for Premier League links in first 10 rows
            pl_links = 0
            for row in rows[:10]:
                for cell in row.find_all(['td', 'th']):
                    for link in cell.find_all('a'):
                        href = link.get('href', '')
                        if '/matches/' in href and 'Premier-League' in href:
                            pl_links += 1
                            if pl_links <= 3:
                                print(f"   PL Link: {href}")
            
            print(f"🎯 Premier League links found: {pl_links}")
        else:
            print("❌ No sched table found")
            print("Available table IDs:")
            for table in tables[:10]:
                table_id = table.get('id', 'no-id')
                print(f"   - {table_id}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(minimal_test())