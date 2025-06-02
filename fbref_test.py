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
import re

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

def test_fbref_match_scraping():
    """Test scraping a specific FBref match page"""
    match_url = "https://fbref.com/en/matches/3a6836b4/Burnley-Manchester-City-August-11-2023-Premier-League"
    
    print(f"Testing scraping for match: {match_url}")
    
    # Setup the driver
    driver = setup_driver()
    if not driver:
        print("Failed to set up ChromeDriver. Test cannot continue.")
        return False
    
    try:
        # Navigate to the match page
        print(f"Navigating to {match_url}")
        driver.get(match_url)
        time.sleep(5)  # Wait for page to load
        
        # Get the page source
        page_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Print the title to verify we're on the right page
        title = soup.title.text if soup.title else "No title found"
        print(f"Page title: {title}")
        
        # Extract team names from the title
        if "vs." in title:
            title_parts = title.split("vs.")
            if len(title_parts) >= 2:
                home_team = title_parts[0].strip()
                away_team = title_parts[1].split("Match Report")[0].strip()
                print(f"Teams from title: {home_team} vs {away_team}")
        
        # Find the scorebox which contains team names and scores
        scorebox = soup.find("div", {"class": "scorebox"})
        if scorebox:
            print("Found scorebox element")
            
            # Extract team names using different methods
            # Method 1: Look for itemprop="name"
            teams = scorebox.find_all("div", {"itemprop": "name"})
            if teams and len(teams) >= 2:
                home_team = teams[0].get_text().strip()
                away_team = teams[1].get_text().strip()
                print(f"Teams (Method 1): {home_team} vs {away_team}")
            
            # Method 2: Look for team divs
            team_divs = scorebox.find_all("div", {"class": "team"})
            if team_divs and len(team_divs) >= 2:
                for i, team_div in enumerate(team_divs[:2]):
                    team_name_elem = team_div.find("a")
                    if team_name_elem:
                        team_name = team_name_elem.get_text().strip()
                        print(f"Team {i+1} (Method 2): {team_name}")
            
            # Method 3: Look for any links to team pages
            team_links = scorebox.find_all("a", href=lambda href: href and "/en/squads/" in href)
            if team_links and len(team_links) >= 2:
                home_team = team_links[0].get_text().strip()
                away_team = team_links[1].get_text().strip()
                print(f"Teams (Method 3): {home_team} vs {away_team}")
            
            # Extract scores
            scores = scorebox.find_all("div", {"class": "score"})
            if scores and len(scores) >= 2:
                home_score = scores[0].get_text().strip()
                away_score = scores[1].get_text().strip()
                print(f"Score: {home_score} - {away_score}")
            else:
                print("Could not find scores in the expected format")
        else:
            print("Could not find scorebox element")
        
        # Find all tables on the page
        tables = soup.find_all("table")
        print(f"Found {len(tables)} tables on the page")
        
        # Look for tables with stats in their ID or class
        stats_tables = []
        for table in tables:
            table_id = table.get("id", "")
            table_class = " ".join(table.get("class", []))
            if "stats" in table_id.lower() or "stats" in table_class.lower():
                stats_tables.append(table)
        
        print(f"Found {len(stats_tables)} stats tables")
        
        # Print the IDs of the stats tables
        for i, table in enumerate(stats_tables):
            table_id = table.get("id", "No ID")
            print(f"Stats Table {i+1} ID: {table_id}")
            
            # Try to determine which team this table is for
            table_header = table.find("caption")
            if table_header:
                header_text = table_header.get_text().strip()
                print(f"  Table header: {header_text}")
            
            # Print column headers
            headers = table.find_all("th")
            if headers:
                header_texts = [h.get_text().strip() for h in headers[:5]]  # First 5 headers
                print(f"  Column headers: {header_texts}")
            
            # Print a sample row
            rows = table.find_all("tr")
            if len(rows) > 1:  # Skip header row
                sample_row = rows[1]
                cells = sample_row.find_all(["td", "th"])
                sample_data = [cell.get_text().strip() for cell in cells[:5]]  # First 5 cells
                print(f"  Sample data: {sample_data}")
        
        # Look for player stats tables
        player_tables = []
        for table in tables:
            table_id = table.get("id", "")
            if "stats_" in table_id.lower() and not "summary" in table_id.lower():
                player_tables.append(table)
        
        print(f"Found {len(player_tables)} player stats tables")
        
        # Print the IDs of the player stats tables
        for i, table in enumerate(player_tables):
            table_id = table.get("id", "No ID")
            print(f"Player Stats Table {i+1} ID: {table_id}")
            
            # Try to determine which team this table is for
            table_header = table.find("caption")
            if table_header:
                header_text = table_header.get_text().strip()
                print(f"  Table header: {header_text}")
            
            # Print a sample player row
            rows = table.find_all("tr")
            if len(rows) > 1:  # Skip header row
                sample_row = rows[1]
                cells = sample_row.find_all(["td", "th"])
                player_name_cell = sample_row.find("th", {"data-stat": "player"})
                if player_name_cell:
                    player_name = player_name_cell.get_text().strip()
                    print(f"  Player: {player_name}")
                
                # Get some sample stats
                sample_stats = []
                for cell in cells[:5]:
                    stat_name = cell.get("data-stat", "unknown")
                    stat_value = cell.get_text().strip()
                    sample_stats.append(f"{stat_name}: {stat_value}")
                
                print(f"  Sample stats: {sample_stats}")
        
        # Take a screenshot for debugging
        screenshot_path = "/tmp/fbref_match.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Close the driver
        driver.quit()
        
        print("Test completed successfully")
        return True
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        if driver:
            driver.quit()
        return False

if __name__ == "__main__":
    test_fbref_match_scraping()