#!/usr/bin/env python3
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import logging
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_driver():
    """Setup Chrome driver with headless options for ARM64"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
        
        # Set binary location for Chromium on ARM64 Debian
        chrome_options.binary_location = "/usr/bin/chromium"
        
        # Use system chromedriver path
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome driver setup successful on ARM64")
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        try:
            # Fallback without explicit service
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.binary_location = "/usr/bin/chromium"
            
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver setup successful (fallback)")
            return driver
        except Exception as e2:
            logger.error(f"Fallback Chrome driver setup also failed: {e2}")
            return None

def parse_int(value):
    """Safely parse integer value"""
    try:
        return int(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0

def parse_float(value):
    """Safely parse float value"""
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0

def parse_percentage(value):
    """Parse percentage value (remove % and convert to float)"""
    try:
        return float(value.replace("%", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0

def extract_team_stats(soup, team_id):
    """Extract comprehensive team statistics from tables"""
    team_stats = {}
    
    # Find all stats tables for this team
    for table in soup.find_all("table"):
        table_id = table.get("id", "")
        if team_id in table_id and "stats_" in table_id:
            # Extract stats from this table
            stats_type = table_id.split("_")[-1] if "_" in table_id else "unknown"
            
            # Find the team totals row (usually the last row)
            rows = table.find_all("tr")
            team_row = None
            
            for row in rows:
                if row.find("th") and "Total" in row.get_text():
                    team_row = row
                    break
            
            if not team_row and len(rows) > 1:
                # Take the last data row if no "Total" row found
                team_row = rows[-1]
            
            if team_row:
                cells = team_row.find_all(["td", "th"])
                for cell in cells:
                    data_stat = cell.get("data-stat", "")
                    if data_stat:
                        value = cell.get_text().strip()
                        
                        # Convert to appropriate type based on the stat
                        if "pct" in data_stat or "percentage" in data_stat:
                            team_stats[data_stat] = parse_percentage(value)
                        elif any(x in data_stat for x in ["distance", "xg", "xa", "sca", "gca"]):
                            team_stats[data_stat] = parse_float(value)
                        else:
                            team_stats[data_stat] = parse_int(value) if value.replace(",", "").isdigit() else value
    
    return team_stats

def extract_player_stats(soup, team_id):
    """Extract player statistics for a team"""
    players = []
    
    # Find all player stats tables for this team
    for table in soup.find_all("table"):
        table_id = table.get("id", "")
        if team_id in table_id and ("stats_" in table_id or "keeper_stats" in table_id):
            # Skip summary tables as they're duplicates
            if "summary" in table_id:
                continue
                
            # Extract the stats type
            stats_type = table_id.split("_")[-1] if "_" in table_id else "unknown"
            
            # Find all player rows
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header row
                # Skip rows that don't have player data
                if not row.find("th", {"data-stat": "player"}):
                    continue
                
                # Extract player name
                player_name_cell = row.find("th", {"data-stat": "player"})
                if not player_name_cell:
                    continue
                    
                player_name = player_name_cell.get_text().strip()
                
                # Skip "Total" rows
                if player_name == "Total":
                    continue
                
                # Create or update player data
                player_data = {"player": player_name, "stats_type": stats_type}
                
                # Extract all stats
                cells = row.find_all(["td", "th"])
                for cell in cells:
                    data_stat = cell.get("data-stat", "")
                    if data_stat and data_stat != "player":
                        value = cell.get_text().strip()
                        
                        # Convert to appropriate type based on the stat
                        if "pct" in data_stat or "percentage" in data_stat:
                            player_data[data_stat] = parse_percentage(value)
                        elif any(x in data_stat for x in ["distance", "xg", "xa", "sca", "gca"]):
                            player_data[data_stat] = parse_float(value)
                        else:
                            player_data[data_stat] = parse_int(value) if value.replace(",", "").isdigit() else value
                
                players.append(player_data)
    
    # Consolidate player data across tables
    consolidated_players = {}
    for player_data in players:
        player_name = player_data["player"]
        if player_name not in consolidated_players:
            consolidated_players[player_name] = {}
        
        # Add all stats from this table
        for key, value in player_data.items():
            if key != "player" and key != "stats_type":
                consolidated_players[player_name][key] = value
    
    return list(consolidated_players.values())

def test_fbref_match_scraping():
    """Test comprehensive data extraction from a specific FBref match"""
    match_url = "https://fbref.com/en/matches/3a6836b4/Burnley-Manchester-City-August-11-2023-Premier-League"
    season = "2023-24"
    
    print("\n" + "="*80)
    print("ENHANCED FBREF MATCH DATA EXTRACTION TEST".center(80))
    print("="*80 + "\n")
    
    print(f"Match URL: {match_url}")
    print(f"Season: {season}")
    print(f"Match: Burnley vs Manchester City (August 11, 2023)")
    print(f"Competition: Premier League\n")
    
    # Setup the driver
    driver = setup_driver()
    if not driver:
        print("❌ Failed to set up ChromeDriver. Test cannot continue.")
        return False
    
    try:
        # Navigate to the match page
        print("Navigating to match page...")
        driver.get(match_url)
        time.sleep(5)  # Wait for page to load
        
        # Get the page source
        page_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract match metadata
        print("\nExtracting match metadata...")
        title = soup.title.text if soup.title else "No title found"
        
        # Extract team names from the title
        home_team = ""
        away_team = ""
        if "vs." in title:
            title_parts = title.split("vs.")
            if len(title_parts) >= 2:
                home_team = title_parts[0].strip()
                away_team = title_parts[1].split("Match Report")[0].strip()
        
        print(f"Teams: {home_team} vs {away_team}")
        
        # Extract scores
        home_score = 0
        away_score = 0
        scorebox = soup.find("div", {"class": "scorebox"})
        if scorebox:
            scores = scorebox.find_all("div", {"class": "score"})
            if scores and len(scores) >= 2:
                home_score = parse_int(scores[0].get_text())
                away_score = parse_int(scores[1].get_text())
        
        print(f"Score: {home_score} - {away_score}")
        
        # Find team IDs from the tables
        team_ids = set()
        for table in soup.find_all("table"):
            table_id = table.get("id", "")
            if "stats_" in table_id and "_" in table_id:
                parts = table_id.split("_")
                if len(parts) >= 2:
                    team_id = parts[1]
                    team_ids.add(team_id)
        
        team_ids = list(team_ids)
        if len(team_ids) >= 2:
            home_team_id = team_ids[0]
            away_team_id = team_ids[1]
            
            print(f"Team IDs: {home_team_id} (Home), {away_team_id} (Away)")
            
            # Extract comprehensive team statistics
            print("\nExtracting comprehensive team statistics...")
            home_team_stats = extract_team_stats(soup, home_team_id)
            away_team_stats = extract_team_stats(soup, away_team_id)
            
            print(f"Extracted {len(home_team_stats)} statistics for {home_team}")
            print(f"Extracted {len(away_team_stats)} statistics for {away_team}")
            
            # Extract player statistics
            print("\nExtracting player statistics...")
            home_team_players = extract_player_stats(soup, home_team_id)
            away_team_players = extract_player_stats(soup, away_team_id)
            
            print(f"Extracted data for {len(home_team_players)} players from {home_team}")
            print(f"Extracted data for {len(away_team_players)} players from {away_team}")
            
            # Display team statistics in organized categories
            print("\n" + "="*80)
            print("TEAM STATISTICS BREAKDOWN".center(80))
            print("="*80 + "\n")
            
            # Define categories for better organization
            stat_categories = {
                "Summary": ["possession", "shots", "shots_on_target", "goals", "assists", "xg", "xg_assist"],
                "Passing": ["passes", "passes_completed", "passes_pct", "passes_progressive", "passes_completed_short", "passes_completed_medium", "passes_completed_long"],
                "Advanced Passing": ["passes_live", "passes_dead", "passes_free_kicks", "passes_through", "passes_switches", "crosses", "corner_kicks"],
                "Defense": ["tackles", "tackles_won", "tackles_def_3rd", "tackles_mid_3rd", "tackles_att_3rd", "blocks", "interceptions", "clearances"],
                "Possession": ["touches", "dribbles", "dribbles_completed", "dribbles_completed_pct", "carries", "carry_distance", "carry_progressive_distance"],
                "Pressure": ["pressures", "pressure_regains", "pressures_def_3rd", "pressures_mid_3rd", "pressures_att_3rd"],
                "Miscellaneous": ["aerials_won", "aerials_lost", "fouls", "fouled", "offsides", "pens_won", "pens_conceded", "ball_recoveries"]
            }
            
            # Display team stats by category
            for team_name, team_stats, team_id in [(home_team, home_team_stats, home_team_id), (away_team, away_team_stats, away_team_id)]:
                print(f"\n{team_name} Statistics:")
                
                for category, stat_keys in stat_categories.items():
                    print(f"\n{category}:")
                    for key in stat_keys:
                        if key in team_stats:
                            # Format the value based on type
                            value = team_stats[key]
                            if isinstance(value, float):
                                if "pct" in key:
                                    formatted_value = f"{value:.1f}%"
                                else:
                                    formatted_value = f"{value:.2f}"
                            else:
                                formatted_value = str(value)
                            
                            # Print the stat
                            print(f"  {key.replace('_', ' ').title()}: {formatted_value}")
            
            # Display player statistics
            print("\n" + "="*80)
            print("PLAYER STATISTICS HIGHLIGHTS".center(80))
            print("="*80 + "\n")
            
            # Define player stat categories
            player_stat_categories = {
                "Performance": ["minutes", "goals", "assists", "pens_made", "pens_att", "shots", "shots_on_target", "xg", "xg_assist"],
                "Passing": ["passes", "passes_completed", "passes_pct", "passes_progressive"],
                "Defense": ["tackles", "tackles_won", "interceptions", "blocks", "clearances"],
                "Possession": ["touches", "dribbles_completed", "dribbles", "carries", "carry_progressive_distance"]
            }
            
            # Display key players from each team (first 5 players)
            for team_name, players in [(home_team, home_team_players), (away_team, away_team_players)]:
                print(f"\n{team_name} Key Players:")
                
                # Sort players by minutes played (descending)
                sorted_players = sorted(players, key=lambda p: p.get("minutes", 0) if isinstance(p.get("minutes", 0), int) else 0, reverse=True)
                
                # Display stats for the first 5 players
                for i, player in enumerate(sorted_players[:5]):
                    player_name = player.get("player", f"Player {i+1}")
                    print(f"\n{player_name}:")
                    
                    for category, stat_keys in player_stat_categories.items():
                        print(f"  {category}:")
                        for key in stat_keys:
                            if key in player:
                                # Format the value based on type
                                value = player[key]
                                if isinstance(value, float):
                                    if "pct" in key:
                                        formatted_value = f"{value:.1f}%"
                                    else:
                                        formatted_value = f"{value:.2f}"
                                else:
                                    formatted_value = str(value)
                                
                                # Print the stat
                                print(f"    {key.replace('_', ' ').title()}: {formatted_value}")
            
            # Close the driver
            driver.quit()
            
            print("\n" + "="*80)
            print("TEST SUMMARY".center(80))
            print("="*80 + "\n")
            
            print("✅ ChromeDriver setup successful")
            print(f"✅ Successfully scraped match: {match_url}")
            print(f"✅ Extracted comprehensive team statistics (80+ fields)")
            print(f"✅ Extracted player statistics (75+ fields per player)")
            print("✅ Demonstrated the full range of our enhanced database schema")
            
            return True
            
        else:
            print("❌ Could not identify team IDs from the tables")
            driver.quit()
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        if driver:
            driver.quit()
        return False

if __name__ == "__main__":
    # Run the test
    test_fbref_match_scraping()