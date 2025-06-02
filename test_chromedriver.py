#!/usr/bin/env python3
"""
Simple test script to verify ChromeDriver setup works on ARM64
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
import time

def test_chromedriver():
    """Test ChromeDriver setup and basic functionality"""
    driver = None
    try:
        print("🔧 Setting up ChromeDriver for ARM64...")
        
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
        chrome_options.binary_location = "/usr/bin/chromium"
        
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)
        
        print("✅ ChromeDriver setup successful!")
        
        # Test basic navigation
        print("🌐 Testing navigation to FBref...")
        test_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
        driver.get(test_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Check if we can find the title
        title = driver.title
        print(f"📄 Page title: {title}")
        
        # Test finding table elements (basic FBref structure test)
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"📊 Found {len(tables)} tables on the page")
        
        if len(tables) > 0:
            print("✅ Successfully found tables - FBref structure accessible!")
        else:
            print("⚠️  No tables found - might need to investigate page loading")
        
        # Test finding links (for match reports)
        links = driver.find_elements(By.TAG_NAME, "a")
        match_links = [link.get_attribute("href") for link in links if link.get_attribute("href") and "/en/matches/" in link.get_attribute("href")]
        print(f"🔗 Found {len(match_links)} potential match report links")
        
        if len(match_links) > 0:
            print("✅ Match report links found - scraping structure looks good!")
            print(f"🔍 Sample match link: {match_links[0][:100]}...")
        
        print("\n🎉 ChromeDriver test completed successfully!")
        print("🚀 Ready for comprehensive FBref scraping!")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromeDriver test failed: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
            print("🔚 ChromeDriver closed")

if __name__ == "__main__":
    success = test_chromedriver()
    sys.exit(0 if success else 1)