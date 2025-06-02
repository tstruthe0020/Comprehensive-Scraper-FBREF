#!/usr/bin/env python3
"""
Step by step debug of the new approach
"""

import asyncio
import sys
sys.path.append('/app/backend')

async def step_by_step_debug():
    from server import scraper
    from bs4 import BeautifulSoup
    
    print("🔍 STEP BY STEP DEBUG")
    print("="*40)
    
    success = await scraper.setup_browser()
    if not success:
        print("❌ Browser setup failed")
        return
    
    print("✅ Browser setup successful")
    
    # Step 1: Navigate to fixtures page
    fixtures_url = "https://fbref.com/en/comps/9/2023-2024/schedule/2023-2024-Premier-League-Scores-and-Fixtures"
    print(f"📡 Navigating to: {fixtures_url}")
    
    try:
        await scraper.navigate_with_retry(fixtures_url)
        print("✅ Navigation successful")
        
        # Step 2: Get content and find table
        content = await scraper.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        tables = soup.find_all('table')
        print(f"📊 Found {len(tables)} tables")
        
        # Step 3: Find the correct table
        target_table = None
        for table in tables:
            table_id = table.get('id', '')
            if 'sched' in table_id and '2023-2024' in table_id:
                target_table = table
                print(f"✅ Found target table: {table_id}")
                break
        
        if not target_table:
            print("❌ Target table not found")
            return
        
        # Step 4: Look for Premier League match URLs
        rows = target_table.find_all('tr')
        print(f"📊 Table has {len(rows)} rows")
        
        match_urls = []
        for row_idx, row in enumerate(rows[1:6]):  # Check first 5 data rows
            cells = row.find_all(['td', 'th'])
            
            for cell in cells:
                links = cell.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    if '/matches/' in href and 'Premier-League' in href:
                        match_url = f"https://fbref.com{href}"
                        if match_url not in match_urls:
                            match_urls.append(match_url)
                            print(f"✅ Found match URL: {match_url}")
        
        print(f"📊 Total unique match URLs found: {len(match_urls)}")
        
        if not match_urls:
            print("❌ No Premier League match URLs found")
            return
        
        # Step 5: Test extracting team names from one match
        test_url = match_urls[0]
        print(f"\n🧪 Testing team extraction from: {test_url}")
        
        await scraper.navigate_with_retry(test_url)
        match_content = await scraper.page.content()
        match_soup = BeautifulSoup(match_content, 'html.parser')
        
        metadata = scraper.extract_match_metadata(match_soup)
        home_team = metadata.get('home_team', '')
        away_team = metadata.get('away_team', '')
        
        if home_team and away_team:
            print(f"✅ Successfully extracted: {home_team} vs {away_team}")
            print("🎉 NEW APPROACH WORKS!")
        else:
            print(f"❌ Failed to extract teams: home='{home_team}', away='{away_team}'")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(step_by_step_debug())