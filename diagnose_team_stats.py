#!/usr/bin/env python3
"""
Diagnose team stats extraction specifically
"""

import asyncio
import sys
sys.path.append('/app/backend')

from csv_scraper import CSVMatchReportScraper
from bs4 import BeautifulSoup

async def diagnose_team_stats():
    """Specifically diagnose why team stats aren't being extracted"""
    
    test_url = "https://fbref.com/en/matches/cc5b4244/Manchester-United-Fulham-August-16-2024-Premier-League"
    
    scraper = CSVMatchReportScraper(rate_limit_delay=1, headless=True)
    
    try:
        if not await scraper.setup_browser():
            print("❌ Browser setup failed")
            return
        
        print(f"🔍 Diagnosing team stats extraction for: {test_url}")
        
        await scraper.page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
        await scraper.page.wait_for_timeout(3000)
        
        content = await scraper.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"Found {len(tables)} total tables on the page")
        
        team_stats_tables = []
        
        for i, table in enumerate(tables):
            table_id = table.get('id', f'no_id_{i}')
            table_class = table.get('class', [])
            
            # Check for team stats indicators
            headers = table.find_all('th')
            header_texts = [th.get_text(strip=True).lower() for th in headers]
            header_data_stats = [th.get('data-stat', '') for th in headers]
            
            # Look for team stats table indicators
            team_indicators = ['possession', 'shots', 'fouls', 'cards']
            data_stat_indicators = ['poss', 'shots', 'fouls', 'cards_yellow']
            
            has_team_headers = any(indicator in ' '.join(header_texts) for indicator in team_indicators)
            has_team_data_stats = any(indicator in header_data_stats for indicator in data_stat_indicators)
            
            print(f"\nTable {i+1}:")
            print(f"  ID: {table_id}")
            print(f"  Class: {table_class}")
            print(f"  Headers: {header_texts[:10]}...")  # First 10 headers
            print(f"  Data-stats: {header_data_stats[:10]}...")  # First 10 data-stats
            print(f"  Has team headers: {has_team_headers}")
            print(f"  Has team data-stats: {has_team_data_stats}")
            
            if has_team_headers or has_team_data_stats:
                team_stats_tables.append((i, table))
                print(f"  ✅ POTENTIAL TEAM STATS TABLE")
                
                # Examine the data in this table
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    print(f"  Rows in tbody: {len(rows)}")
                    
                    for j, row in enumerate(rows[:3]):  # First 3 rows
                        cells = row.find_all(['td', 'th'])
                        row_data = []
                        for cell in cells:
                            data_stat = cell.get('data-stat', '')
                            text = cell.get_text(strip=True)
                            if data_stat:
                                row_data.append(f"{data_stat}={text}")
                            else:
                                row_data.append(text)
                        print(f"    Row {j+1}: {row_data[:5]}...")  # First 5 cells
        
        print(f"\n📊 Summary:")
        print(f"Total tables: {len(tables)}")
        print(f"Potential team stats tables: {len(team_stats_tables)}")
        
        if team_stats_tables:
            print(f"\n🔍 Analyzing the most promising team stats table...")
            table_index, best_table = team_stats_tables[0]
            
            # Use the existing extraction method on this table
            team_stats = {}
            headers = best_table.find_all('th')
            header_texts = [th.get_text(strip=True).lower() for th in headers]
            
            if any(stat in ' '.join(header_texts) for stat in ['possession', 'shots', 'fouls']):
                rows = best_table.find('tbody').find_all('tr') if best_table.find('tbody') else []
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        team_name = cells[0].get_text(strip=True)
                        
                        # Extract stats using data-stat attributes
                        for cell in cells:
                            data_stat = cell.get('data-stat', '')
                            value = cell.get_text(strip=True)
                            
                            if data_stat and value and team_name and team_name not in ['Team', '']:
                                if team_name not in team_stats:
                                    team_stats[team_name] = {}
                                team_stats[team_name][data_stat] = value
            
            print(f"Extracted team stats: {team_stats}")
            
            if team_stats:
                print("✅ Team stats extraction working!")
            else:
                print("❌ Team stats extraction not working - need to improve logic")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(diagnose_team_stats())