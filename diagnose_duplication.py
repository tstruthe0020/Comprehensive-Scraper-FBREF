#!/usr/bin/env python3
"""
Diagnostic script to identify data duplication issues
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import sys
sys.path.append('/app/backend')
from server import FBrefScraper

TEST_URL = "https://fbref.com/en/matches/9c4f2bcd/Brentford-West-Ham-United-September-28-2024-Premier-League"

async def diagnose_duplication():
    print("🔍 DIAGNOSING DATA DUPLICATION ISSUES")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TEST_URL, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        scraper = FBrefScraper()
        metadata = scraper.extract_match_metadata(soup)
        
        print(f"Teams: {metadata.get('home_team')} vs {metadata.get('away_team')}")
        
        # Let's examine the tables in detail for Brentford
        team_name = "Brentford"
        team_id = scraper._get_team_id_from_tables(soup, team_name)
        print(f"\nTeam ID for {team_name}: {team_id}")
        
        # Check each table individually
        stat_categories = ['summary', 'passing', 'defense', 'possession', 'misc']
        
        for category in stat_categories:
            table_id = f"stats_{team_id}_{category}"
            table = soup.find("table", {"id": table_id})
            
            if table:
                print(f"\n📊 TABLE: {table_id}")
                
                # Count rows and see what data we're getting
                rows = table.find_all('tr')
                print(f"   Total rows: {len(rows)}")
                
                # Look for shots data specifically
                shots_cells = table.find_all('td', {'data-stat': 'shots'})
                if shots_cells:
                    print(f"   Shots cells found: {len(shots_cells)}")
                    for i, cell in enumerate(shots_cells[:5]):  # Show first 5
                        value = cell.get_text().strip()
                        print(f"     Cell {i+1}: '{value}'")
                
                # Look for team totals or footer
                footer = table.find('tfoot')
                if footer:
                    print(f"   Has footer: YES")
                    footer_shots = footer.find_all('td', {'data-stat': 'shots'})
                    if footer_shots:
                        for cell in footer_shots:
                            print(f"     Footer shots: '{cell.get_text().strip()}'")
                else:
                    print(f"   Has footer: NO")
                
                # Check if any rows contain "total" 
                total_rows = [row for row in rows if 'total' in row.get_text().lower()]
                print(f"   Rows with 'total': {len(total_rows)}")
        
        # Now let's manually calculate what the shots should be
        print(f"\n🧮 MANUAL SHOTS CALCULATION FOR {team_name}")
        summary_table = soup.find("table", {"id": f"stats_{team_id}_summary"})
        if summary_table:
            all_shots = summary_table.find_all('td', {'data-stat': 'shots'})
            print(f"All shots cells in summary table: {len(all_shots)}")
            
            total_shots = 0
            for i, cell in enumerate(all_shots):
                value = cell.get_text().strip()
                try:
                    shots = int(value) if value else 0
                    print(f"  Player {i+1}: {shots} shots")
                    total_shots += shots
                except ValueError:
                    print(f"  Player {i+1}: '{value}' (non-numeric)")
            
            print(f"  CALCULATED TOTAL: {total_shots} shots")
            print(f"  CURRENT EXTRACTION: {scraper.extract_team_stats(soup, team_name).get('shots', 0)} shots")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnose_duplication())