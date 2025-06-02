#!/usr/bin/env python3
"""
Test script to debug Playwright fixture extraction
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test_fixture_extraction():
    """Test fixture extraction with detailed debugging"""
    print("🔍 Starting Playwright fixture extraction test...")
    
    playwright = None
    browser = None
    page = None
    
    try:
        # Setup Playwright
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test URL
        test_url = "https://fbref.com/en/comps/9/2023-24/schedule/Premier-League-Scores-and-Fixtures"
        print(f"📡 Navigating to: {test_url}")
        
        # Navigate to page
        await page.goto(test_url, wait_until='networkidle')
        print("✅ Page loaded successfully")
        
        # Get page title
        title = await page.title()
        print(f"📄 Page title: {title}")
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"📊 Found {len(tables)} tables on page")
        
        # Log table information
        for i, table in enumerate(tables):
            table_id = table.get('id', f'no-id-{i}')
            table_class = table.get('class', ['no-class'])
            rows = table.find_all('tr')
            print(f"  Table {i}: ID='{table_id}', Class={table_class}, Rows={len(rows)}")
            
            # If this looks like a fixtures table, examine it closer
            if 'sched' in table_id.lower() or len(rows) > 20:
                print(f"    🎯 Examining table {i} in detail:")
                
                # Look at first few rows
                for row_idx, row in enumerate(rows[:5]):
                    cells = row.find_all(['td', 'th'])
                    cell_texts = [cell.get_text(strip=True)[:15] for cell in cells[:8]]
                    print(f"      Row {row_idx}: {cell_texts}")
                    
                    # Look for links in each cell
                    for cell_idx, cell in enumerate(cells[:8]):
                        links = cell.find_all('a')
                        if links:
                            for link in links:
                                href = link.get('href', '')
                                if '/matches/' in href:
                                    print(f"        🔗 MATCH LINK found in cell {cell_idx}: {href}")
        
        print("✅ Fixture extraction test completed")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        
    finally:
        # Cleanup
        if page:
            await page.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_fixture_extraction())