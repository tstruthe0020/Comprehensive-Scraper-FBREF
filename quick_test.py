#!/usr/bin/env python3
"""
Quick test to see what links are actually on the FBref page
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

def quick_test():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Try current season first
        url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
        print(f"Accessing current season: {url}")
        
        driver.get(url)
        time.sleep(5)
        
        # Quick check for match links
        all_links = driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(all_links)} total links")
        
        # Look for any match links 
        match_links = []
        for link in all_links[:500]:  # Just check first 500 links
            href = link.get_attribute("href")
            text = link.text.strip()
            
            if href and "/en/matches/" in href and len(href.split("/")) > 5:
                match_links.append((href, text))
                if len(match_links) >= 10:  # Stop after finding 10
                    break
        
        print(f"\n⚽ Found {len(match_links)} match links:")
        for i, (href, text) in enumerate(match_links):
            print(f"   {i+1}. '{text}' -> {href}")
        
        # Test one match if found
        if match_links:
            test_href = match_links[0][0]
            print(f"\n🧪 Testing match: {test_href}")
            
            driver.get(test_href)
            time.sleep(3)
            
            title = driver.title
            print(f"📄 Match page title: {title}")
            
            # Quick check for scorebox
            try:
                scorebox = driver.find_element(By.CLASS_NAME, "scorebox")
                print("✅ Found scorebox on match page")
            except:
                print("❌ No scorebox found")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    quick_test()