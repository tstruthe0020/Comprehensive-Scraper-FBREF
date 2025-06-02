#!/usr/bin/env python3
import asyncio
import logging
from playwright.async_api import async_playwright
import sys
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_alternative_fixtures_extraction():
    """Test an alternative approach to extract fixtures"""
    logger.info("Testing alternative fixtures extraction approach...")
    
    # Setup Playwright browser
    async with async_playwright() as playwright:
        logger.info("Setting up Playwright browser...")
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent to avoid detection
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        })
        
        # Navigate to the fixtures page
        season = "2023-24"
        fixtures_url = f"https://fbref.com/en/comps/9/{season}/schedule/Premier-League-Scores-and-Fixtures"
        logger.info(f"Navigating to fixtures URL: {fixtures_url}")
        
        try:
            await page.goto(fixtures_url)
            await page.wait_for_timeout(3000)  # Wait for page to load
            
            # Check if the page loaded correctly
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Try a more general approach - look for any table with schedule data
            logger.info("Looking for any table with schedule/fixtures data...")
            
            # Look for links to match reports directly
            match_links = await page.query_selector_all("a[href*='/en/matches/']")
            logger.info(f"Found {len(match_links)} match links on the page")
            
            # Print the first few links
            match_urls = []
            for i, link in enumerate(match_links[:10]):
                href = await link.get_attribute("href")
                text = await link.text_content()
                if href and "/en/matches/" in href and len(href.split("/")) > 5:
                    # Convert relative URLs to absolute
                    if href.startswith("/"):
                        href = f"https://fbref.com{href}"
                    match_urls.append(href)
                    logger.info(f"Match link {i+1}: {text} -> {href}")
            
            logger.info(f"Found {len(match_urls)} valid match URLs")
            
            # Try to find the fixtures table by looking for a table with "Date" and "Score" columns
            tables = await page.query_selector_all("table")
            logger.info(f"Found {len(tables)} tables on the page")
            
            fixtures_table = None
            for i, table in enumerate(tables):
                table_text = await table.text_content()
                if "Date" in table_text and "Score" in table_text and "Referee" in table_text:
                    logger.info(f"Found potential fixtures table (Table {i+1})")
                    fixtures_table = table
                    break
            
            if fixtures_table:
                # Try to extract match links from this table
                table_links = await fixtures_table.query_selector_all("a[href*='/en/matches/']")
                logger.info(f"Found {len(table_links)} match links in the fixtures table")
                
                # Print the first few links
                table_match_urls = []
                for i, link in enumerate(table_links[:10]):
                    href = await link.get_attribute("href")
                    text = await link.text_content()
                    if href and "/en/matches/" in href and len(href.split("/")) > 5:
                        # Convert relative URLs to absolute
                        if href.startswith("/"):
                            href = f"https://fbref.com{href}"
                        table_match_urls.append(href)
                        logger.info(f"Table match link {i+1}: {text} -> {href}")
                
                logger.info(f"Found {len(table_match_urls)} valid match URLs in the fixtures table")
            else:
                logger.error("Could not find a fixtures table with Date and Score columns")
            
            # Take a screenshot for debugging
            await page.screenshot(path="fixtures_page_alt.png")
            logger.info("Saved screenshot to fixtures_page_alt.png")
            
            # Return the match URLs
            return match_urls
            
        except Exception as e:
            logger.error(f"Error during alternative fixtures extraction: {e}")
            return []
        finally:
            await browser.close()

async def test_match_data_extraction(match_url):
    """Test extracting data from a match page"""
    logger.info(f"Testing match data extraction for: {match_url}")
    
    # Setup Playwright browser
    async with async_playwright() as playwright:
        logger.info("Setting up Playwright browser...")
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent to avoid detection
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        })
        
        try:
            await page.goto(match_url)
            await page.wait_for_timeout(2000)  # Wait for page to load
            
            # Extract team names and score from the scorebox
            scorebox = await page.query_selector("div.scorebox")
            if scorebox:
                # Get team names
                team_elements = await scorebox.query_selector_all("div[itemprop='name']")
                if len(team_elements) >= 2:
                    home_team = await team_elements[0].text_content()
                    away_team = await team_elements[1].text_content()
                    logger.info(f"Home team: {home_team.strip()}")
                    logger.info(f"Away team: {away_team.strip()}")
                
                # Get scores
                score_elements = await scorebox.query_selector_all("div.score")
                if len(score_elements) >= 2:
                    home_score = await score_elements[0].text_content()
                    away_score = await score_elements[1].text_content()
                    logger.info(f"Score: {home_score.strip()} - {away_score.strip()}")
            else:
                logger.error("Scorebox not found!")
            
            # Extract match date
            date_element = await page.query_selector("span.venuetime")
            if date_element:
                date_value = await date_element.get_attribute("data-venue-date")
                logger.info(f"Match date: {date_value}")
            else:
                logger.error("Date element not found!")
            
            # Try different selectors for the info box
            info_box = await page.query_selector("div#info_box, div.info_box, div#meta")
            if info_box:
                info_text = await info_box.text_content()
                
                # Extract referee
                referee_match = re.search(r"Referee:\s*([^,\n]+)", info_text)
                if referee_match:
                    logger.info(f"Referee: {referee_match.group(1).strip()}")
                
                # Extract stadium
                stadium_match = re.search(r"Venue:\s*([^,\n]+)", info_text)
                if stadium_match:
                    logger.info(f"Stadium: {stadium_match.group(1).strip()}")
            else:
                logger.error("Info box not found with any selector!")
                
                # Try to find any element that might contain referee info
                page_text = await page.content()
                referee_match = re.search(r"Referee:\s*([^,\n<]+)", page_text)
                if referee_match:
                    logger.info(f"Referee (from page content): {referee_match.group(1).strip()}")
                
                stadium_match = re.search(r"Venue:\s*([^,\n<]+)", page_text)
                if stadium_match:
                    logger.info(f"Stadium (from page content): {stadium_match.group(1).strip()}")
            
            # Take a screenshot for debugging
            screenshot_path = f"match_page_{match_url.split('/')[-2]}.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            return {
                "match_url": match_url,
                "home_team": home_team.strip() if 'home_team' in locals() else "",
                "away_team": away_team.strip() if 'away_team' in locals() else "",
                "home_score": int(home_score.strip()) if 'home_score' in locals() and home_score.strip().isdigit() else 0,
                "away_score": int(away_score.strip()) if 'away_score' in locals() and away_score.strip().isdigit() else 0,
                "match_date": date_value if 'date_value' in locals() else ""
            }
            
        except Exception as e:
            logger.error(f"Error during match data extraction: {e}")
            return None
        finally:
            await browser.close()

async def main():
    """Run the tests"""
    logger.info("Starting alternative tests for FBref scraper")
    
    # Test alternative fixtures extraction
    logger.info("=== Testing Alternative Fixtures Extraction ===")
    match_urls = await test_alternative_fixtures_extraction()
    
    if match_urls:
        logger.info(f"Successfully extracted {len(match_urls)} match URLs")
        
        # Test match data extraction for the first few matches
        logger.info("=== Testing Match Data Extraction ===")
        for i, match_url in enumerate(match_urls[:3]):
            logger.info(f"Testing match {i+1}: {match_url}")
            match_data = await test_match_data_extraction(match_url)
            if match_data:
                logger.info(f"Successfully extracted data for match {i+1}")
                logger.info(f"Match data: {match_data}")
            else:
                logger.error(f"Failed to extract data for match {i+1}")
    else:
        logger.error("Failed to extract any match URLs")

if __name__ == "__main__":
    asyncio.run(main())