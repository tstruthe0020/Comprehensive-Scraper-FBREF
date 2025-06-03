#!/usr/bin/env python3
"""
Updated team stats extraction to handle the correct table structure
"""

import asyncio
import sys
sys.path.append('/app/backend')

from csv_scraper import CSVMatchReportScraper
from bs4 import BeautifulSoup
import re

async def test_improved_team_stats():
    """Test improved team stats extraction"""
    
    test_url = "https://fbref.com/en/matches/cc5b4244/Manchester-United-Fulham-August-16-2024-Premier-League"
    
    scraper = CSVMatchReportScraper(rate_limit_delay=1, headless=True)
    
    try:
        if not await scraper.setup_browser():
            print("❌ Browser setup failed")
            return
        
        print(f"🔍 Testing improved team stats extraction...")
        
        await scraper.page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
        await scraper.page.wait_for_timeout(3000)
        
        content = await scraper.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find team stats using the new method
        team_stats = extract_team_stats_improved(soup)
        
        print(f"✅ Improved extraction results:")
        print(f"Teams found: {list(team_stats.keys())}")
        
        for team, stats in team_stats.items():
            print(f"\n{team}:")
            for stat, value in stats.items():
                print(f"  {stat}: {value}")
        
        if len(team_stats) >= 2:
            print(f"\n🎉 SUCCESS: Found stats for {len(team_stats)} teams!")
        else:
            print(f"\n⚠️ PARTIAL: Found stats for {len(team_stats)} teams")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await scraper.cleanup()

def extract_team_stats_improved(soup):
    """Improved team stats extraction that handles the actual FBREF structure"""
    
    team_stats = {}
    
    try:
        # Find all tables
        tables = soup.find_all('table')
        
        for table in tables:
            # Look for the team comparison table
            headers = table.find_all('th')
            header_texts = [th.get_text(strip=True).lower() for th in headers]
            
            # Check if this looks like the team comparison table
            # It should have team names in first two headers and stats in the rest
            if len(header_texts) >= 3:
                # Look for pattern: [team1, team2, stat1, stat2, ...]
                potential_teams = header_texts[:2]
                potential_stats = header_texts[2:]
                
                # Check if we have team-like names and stats-like names
                has_team_indicators = any(word in ' '.join(potential_teams) for word in ['united', 'manchester', 'fulham', 'chelsea', 'arsenal', 'liverpool', 'city'])
                has_stat_indicators = any(word in ' '.join(potential_stats) for word in ['possession', 'shots', 'passing', 'accuracy', 'saves', 'cards', 'fouls'])
                
                if has_team_indicators and has_stat_indicators:
                    print(f"Found team comparison table!")
                    print(f"Teams: {potential_teams}")
                    print(f"Stats: {potential_stats}")
                    
                    # Extract the data from this table
                    tbody = table.find('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        
                        # Initialize team stats
                        team1_name = potential_teams[0].title()
                        team2_name = potential_teams[1].title()
                        team_stats[team1_name] = {}
                        team_stats[team2_name] = {}
                        
                        current_stat = None
                        
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            
                            print(f"Row: {cell_texts}")
                            
                            if len(cell_texts) == 1:
                                # This is a stat name row
                                current_stat = cell_texts[0].lower().replace(' ', '_')
                                print(f"  Stat: {current_stat}")
                            elif len(cell_texts) == 2 and current_stat:
                                # This is a data row with two values
                                team1_value = cell_texts[0]
                                team2_value = cell_texts[1]
                                
                                # Store the values
                                team_stats[team1_name][current_stat] = team1_value
                                team_stats[team2_name][current_stat] = team2_value
                                
                                print(f"  {team1_name}: {current_stat} = {team1_value}")
                                print(f"  {team2_name}: {current_stat} = {team2_value}")
                            elif len(cell_texts) >= 2:
                                # Multiple columns - might be team names or other format
                                if cell_texts[0] in potential_teams and cell_texts[1] in potential_teams:
                                    # This is the header row, skip
                                    continue
                    
                    break  # Found our table, stop looking
        
        return team_stats
        
    except Exception as e:
        print(f"Error in improved extraction: {e}")
        return {}

if __name__ == "__main__":
    asyncio.run(test_improved_team_stats())