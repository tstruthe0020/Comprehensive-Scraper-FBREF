#!/usr/bin/env python3
import asyncio
import logging
from playwright.async_api import async_playwright
import sys
import re
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_direct_match_extraction():
    """Test extracting data directly from a known match URL"""
    logger.info("Testing direct match extraction...")
    
    # Known match URL from the 2023-24 season
    match_url = "https://fbref.com/en/matches/3a6836b4/Burnley-Manchester-City-August-11-2023-Premier-League"
    
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
            logger.info(f"Navigating to match URL: {match_url}")
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
            
            # Try different selectors for the info box
            info_box = await page.query_selector("div#meta")
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
                logger.error("Info box not found with div#meta selector!")
            
            # Extract team stats
            logger.info("Extracting team stats...")
            
            # Look for stats tables
            stats_tables = await page.query_selector_all("table.stats_table")
            logger.info(f"Found {len(stats_tables)} stats tables")
            
            # Extract possession stats
            possession_data = {}
            for table in stats_tables:
                table_text = await table.text_content()
                if "Possession" in table_text:
                    logger.info("Found possession stats table")
                    
                    # Try to extract possession percentages
                    rows = await table.query_selector_all("tr")
                    for row in rows:
                        row_text = await row.text_content()
                        if "Possession" in row_text:
                            cells = await row.query_selector_all("td")
                            if len(cells) >= 2:
                                home_poss = await cells[0].text_content()
                                away_poss = await cells[1].text_content()
                                logger.info(f"Possession: {home_poss.strip()} - {away_poss.strip()}")
                                possession_data = {
                                    "home_possession": float(home_poss.strip().replace("%", "")),
                                    "away_possession": float(away_poss.strip().replace("%", ""))
                                }
                                break
            
            # Extract shots stats
            shots_data = {}
            for table in stats_tables:
                table_text = await table.text_content()
                if "Shots" in table_text:
                    logger.info("Found shots stats table")
                    
                    # Try to extract shots data
                    rows = await table.query_selector_all("tr")
                    for row in rows:
                        row_text = await row.text_content()
                        if "Shots" in row_text and "Shots on Target" not in row_text:
                            cells = await row.query_selector_all("td")
                            if len(cells) >= 2:
                                home_shots = await cells[0].text_content()
                                away_shots = await cells[1].text_content()
                                logger.info(f"Shots: {home_shots.strip()} - {away_shots.strip()}")
                                shots_data["home_shots"] = int(home_shots.strip())
                                shots_data["away_shots"] = int(away_shots.strip())
                        
                        if "Shots on Target" in row_text:
                            cells = await row.query_selector_all("td")
                            if len(cells) >= 2:
                                home_sot = await cells[0].text_content()
                                away_sot = await cells[1].text_content()
                                logger.info(f"Shots on Target: {home_sot.strip()} - {away_sot.strip()}")
                                shots_data["home_shots_on_target"] = int(home_sot.strip())
                                shots_data["away_shots_on_target"] = int(away_sot.strip())
            
            # Take a screenshot for debugging
            await page.screenshot(path="direct_match_page.png")
            logger.info("Saved screenshot to direct_match_page.png")
            
            # Create match data object
            match_data = {
                "match_url": match_url,
                "home_team": home_team.strip() if 'home_team' in locals() else "",
                "away_team": away_team.strip() if 'away_team' in locals() else "",
                "home_score": int(home_score.strip()) if 'home_score' in locals() and home_score.strip().isdigit() else 0,
                "away_score": int(away_score.strip()) if 'away_score' in locals() and away_score.strip().isdigit() else 0,
                "match_date": date_value if 'date_value' in locals() else "",
                "season": "2023-24"
            }
            
            # Add possession and shots data if available
            if possession_data:
                match_data.update(possession_data)
            
            if shots_data:
                match_data.update(shots_data)
            
            # Save match data to a file for inspection
            with open("match_data.json", "w") as f:
                json.dump(match_data, f, indent=2)
            
            logger.info(f"Match data saved to match_data.json")
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error during direct match extraction: {e}")
            return None
        finally:
            await browser.close()

async def main():
    """Run the direct match extraction test"""
    logger.info("Starting direct match extraction test")
    
    match_data = await test_direct_match_extraction()
    
    if match_data:
        logger.info("Direct match extraction successful!")
        logger.info(f"Match data: {match_data}")
    else:
        logger.error("Direct match extraction failed!")

if __name__ == "__main__":
    asyncio.run(main())