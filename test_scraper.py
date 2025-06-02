#!/usr/bin/env python3
"""
Quick test script to verify FBref scraping functionality
"""

import sys
import os
sys.path.append('/app/backend')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def test_fbref_access():
    """Test basic access to FBref and find match reports"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    driver = None
    try:
        # Initialize driver with service
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome driver initialized successfully")
        
        # Test URL for 2023-24 season
        url = "https://fbref.com/en/comps/9/2023-24/schedule/Premier-League-Scores-and-Fixtures"
        print(f"🔍 Accessing: {url}")
        
        driver.get(url)
        time.sleep(5)
        
        # Get page title
        title = driver.title
        print(f"📄 Page title: {title}")
        
        # Look for match report links with different possible text variations
        possible_link_texts = ["Match Report", "Report", "match report"]
        
        for link_text in possible_link_texts:
            links = driver.find_elements(By.LINK_TEXT, link_text)
            print(f"🔗 Found {len(links)} links with text '{link_text}'")
            
            if links:
                # Print first few link URLs
                for i, link in enumerate(links[:3]):
                    href = link.get_attribute("href")
                    print(f"   {i+1}. {href}")
                break
        
        # Also try partial link text
        partial_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Report")
        print(f"🔗 Found {len(partial_links)} links containing 'Report'")
        
        # Look for score links - these are the actual match report links
        all_links = driver.find_elements(By.TAG_NAME, "a")
        score_links = []
        
        import re
        score_pattern = re.compile(r'^\d+[–-]\d+$')  # Matches patterns like "2-1", "0-0", etc.
        
        for link in all_links:
            href = link.get_attribute("href")
            link_text = link.text.strip()
            
            if href and "/en/matches/" in href:
                # Check if link text looks like a score
                if score_pattern.match(link_text):
                    score_links.append((href, link_text))
                # Also collect any other match links for comparison
                elif len(href.split("/")) > 5:  # Full match URLs
                    print(f"   Other match link: '{link_text}' -> {href}")
        
        print(f"🎯 Found {len(score_links)} score links (match reports):")
        for i, (link, score) in enumerate(score_links[:10]):
            print(f"   {i+1}. Score: '{score}' | URL: {link}")
        
        # Test scraping one specific match if we found any score links
        if score_links:
            print(f"\n🧪 Testing scrape of first match: {score_links[0][0]}")
            test_match_scrape(driver, score_links[0][0])
        else:
            print("\n❌ No score links found - let's examine the table structure more closely")
            
            # Let's look for tables and examine their content
            tables = driver.find_elements(By.TAG_NAME, "table")
            for i, table in enumerate(tables[:3]):  # Just first 3 tables
                print(f"\n📋 Examining table {i+1}:")
                table_id = table.get_attribute("id") or f"table_{i}"
                print(f"   ID: {table_id}")
                
                # Look at rows in this table
                rows = table.find_elements(By.TAG_NAME, "tr")
                for j, row in enumerate(rows[1:6]):  # Skip header, check first 5 data rows
                    # Look for links in this row
                    links_in_row = row.find_elements(By.TAG_NAME, "a")
                    for link in links_in_row:
                        href = link.get_attribute("href") 
                        text = link.text.strip()
                        if href and "/en/matches/" in href:
                            print(f"   Row {j+1}: '{text}' -> {href}")
                            # Check if this looks like a score
                            if re.match(r'.*\d.*[–-].*\d.*', text):
                                print(f"      ⚽ This looks like a score link!")
        
        print("\n✅ Basic access test completed")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()

def test_match_scrape(driver, match_url):
    """Test scraping a specific match report"""
    try:
        print(f"🔍 Loading match: {match_url}")
        driver.get(match_url)
        time.sleep(5)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Try to extract basic metadata
        print("📊 Extracting match data...")
        
        # Look for scorebox
        scorebox = soup.find("div", {"class": "scorebox"})
        if scorebox:
            print("✅ Found scorebox")
            
            # Try to find team names
            teams = scorebox.find_all("div", {"itemprop": "name"})
            if teams:
                print(f"⚽ Teams found: {[team.get_text().strip() for team in teams]}")
            
            # Try to find scores
            scores = scorebox.find_all("div", {"class": "score"})
            if scores:
                print(f"🥅 Scores found: {[score.get_text().strip() for score in scores]}")
        else:
            print("❌ No scorebox found")
        
        # Look for any tables with stats
        tables = soup.find_all("table")
        print(f"📋 Found {len(tables)} tables on the page")
        
        # Look for specific stat tables
        stat_tables = []
        for table in tables:
            table_id = table.get("id", "")
            if "stats_" in table_id:
                stat_tables.append(table_id)
        
        if stat_tables:
            print(f"📈 Stat tables found: {stat_tables}")
        else:
            print("❌ No stat tables found with 'stats_' in ID")
        
        print("✅ Match scrape test completed")
        
    except Exception as e:
        print(f"❌ Error during match scrape: {e}")

if __name__ == "__main__":
    test_fbref_access()