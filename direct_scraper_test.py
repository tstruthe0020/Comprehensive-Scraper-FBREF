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

async def test_fixtures_extraction():
    """Test the fixtures extraction logic directly"""
    logger.info("Testing fixtures extraction directly...")
    
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
            
            # Try to find the fixtures table
            table_id = f"sched_{season}_9_1"
            logger.info(f"Looking for table with ID: {table_id}")
            
            # Check if the table exists
            table_exists = await page.evaluate(f'document.getElementById("{table_id}") !== null')
            
            if table_exists:
                logger.info(f"Table with ID {table_id} found!")
                
                # Try to extract match links
                links = await page.query_selector_all(f"table#{table_id} a[href*='/en/matches/']")
                logger.info(f"Found {len(links)} match links in the table")
                
                # Print the first few links
                for i, link in enumerate(links[:5]):
                    href = await link.get_attribute("href")
                    text = await link.text_content()
                    logger.info(f"Link {i+1}: {text} -> {href}")
            else:
                logger.error(f"Table with ID {table_id} not found!")
                
                # Try to find any tables on the page
                tables = await page.query_selector_all("table")
                logger.info(f"Found {len(tables)} tables on the page")
                
                # Check table IDs
                for i, table in enumerate(tables):
                    table_id = await table.get_attribute("id")
                    logger.info(f"Table {i+1} ID: {table_id}")
                    
                    # If this is a schedule table, check its structure
                    if table_id and "sched_" in table_id:
                        logger.info(f"Found schedule table with ID: {table_id}")
                        
                        # Try to extract match links from this table
                        links = await table.query_selector_all("a[href*='/en/matches/']")
                        logger.info(f"Found {len(links)} match links in this table")
                        
                        # Print the first few links
                        for j, link in enumerate(links[:5]):
                            href = await link.get_attribute("href")
                            text = await link.text_content()
                            logger.info(f"Link {j+1}: {text} -> {href}")
            
            # Take a screenshot for debugging
            await page.screenshot(path="fixtures_page.png")
            logger.info("Saved screenshot to fixtures_page.png")
            
        except Exception as e:
            logger.error(f"Error during fixtures extraction: {e}")
        finally:
            await browser.close()

async def test_match_extraction():
    """Test the match data extraction from a specific match page"""
    logger.info("Testing match data extraction directly...")
    
    # Setup Playwright browser
    async with async_playwright() as playwright:
        logger.info("Setting up Playwright browser...")
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent to avoid detection
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        })
        
        # Navigate to a known match page
        match_url = "https://fbref.com/en/matches/3a6836b4/Burnley-Manchester-City-August-11-2023-Premier-League"
        logger.info(f"Navigating to match URL: {match_url}")
        
        try:
            await page.goto(match_url)
            await page.wait_for_timeout(2000)  # Wait for page to load
            
            # Check if the page loaded correctly
            title = await page.title()
            logger.info(f"Page title: {title}")
            
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
                
            # Extract referee and venue information
            info_box = await page.query_selector("div#info_box, div.info_box")
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
                logger.error("Info box not found!")
            
            # Take a screenshot for debugging
            await page.screenshot(path="match_page.png")
            logger.info("Saved screenshot to match_page.png")
            
        except Exception as e:
            logger.error(f"Error during match extraction: {e}")
        finally:
            await browser.close()

async def main():
    """Run the tests"""
    logger.info("Starting direct tests for FBref scraper")
    
    # Test fixtures extraction
    logger.info("=== Testing Fixtures Extraction ===")
    await test_fixtures_extraction()
    
    # Test match extraction
    logger.info("=== Testing Match Extraction ===")
    await test_match_extraction()

if __name__ == "__main__":
    asyncio.run(main())