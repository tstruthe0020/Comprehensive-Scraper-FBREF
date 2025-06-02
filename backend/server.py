from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio
import pandas as pd
import io
from playwright.async_api import async_playwright
import time
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models
class MatchData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    season: str
    stadium: str
    referee: str
    assistant_referees: List[str] = []
    fourth_official: str = ""
    var_referee: str = ""
    
    # Team Stats - Home Team
    home_possession: float = 0.0
    home_shots: int = 0
    home_shots_on_target: int = 0
    home_expected_goals: float = 0.0
    home_corners: int = 0
    home_tackles: int = 0
    home_fouls_committed: int = 0
    home_fouls_drawn: int = 0
    home_yellow_cards: int = 0
    home_red_cards: int = 0
    home_passing_accuracy: float = 0.0
    home_crosses_completed: int = 0
    home_clearances: int = 0
    home_blocks: int = 0
    home_saves: int = 0
    home_expected_goals_against: float = 0.0
    
    # Team Stats - Away Team
    away_possession: float = 0.0
    away_shots: int = 0
    away_shots_on_target: int = 0
    away_expected_goals: float = 0.0
    away_corners: int = 0
    away_tackles: int = 0
    away_fouls_committed: int = 0
    away_fouls_drawn: int = 0
    away_yellow_cards: int = 0
    away_red_cards: int = 0
    away_passing_accuracy: float = 0.0
    away_crosses_completed: int = 0
    away_clearances: int = 0
    away_blocks: int = 0
    away_saves: int = 0
    away_expected_goals_against: float = 0.0
    
    match_url: str = ""
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

class ScrapingStatus(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str  # "running", "completed", "failed"
    matches_scraped: int = 0
    total_matches: int = 0
    current_match: str = ""
    errors: List[str] = []
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class FilterRequest(BaseModel):
    season: Optional[str] = None
    teams: Optional[List[str]] = []
    referee: Optional[str] = None

class FBrefScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def setup_browser(self):
        """Setup Playwright browser with headless options"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            
            # Set user agent to avoid detection
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
            })
            
            logger.info("Playwright browser setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            return False
    
    def get_season_fixtures_url(self, season: str) -> str:
        """Get the fixtures URL for a specific season"""
        if season == "2024-25":
            return "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
        else:
            return f"https://fbref.com/en/comps/9/{season}/schedule/Premier-League-Scores-and-Fixtures"
    
    async def extract_season_fixtures(self, season: str) -> List[str]:
        """
        Extract all match URLs from a season's fixtures page.
        NEW APPROACH: Only extract match URLs, get team names from individual match pages.
        """
        try:
            fixtures_url = self.get_season_fixtures_url(season)
            logger.info(f"Fetching fixtures from: {fixtures_url}")
            
            await self.page.goto(fixtures_url)
            await self.page.wait_for_timeout(3000)
            
            # Convert season format: 2023-24 -> 2023-2024
            if len(season.split('-')[1]) == 2:  # e.g., "2023-24"
                year_start = season.split('-')[0]
                year_end = "20" + season.split('-')[1]
                season_full = f"{year_start}-{year_end}"
            else:  # Already full format e.g., "2023-2024"
                season_full = season
            
            # Find the fixtures table
            table_id = f"sched_{season_full}_9_1"
            table_selector = f"table#{table_id}"
            
            logger.info(f"Looking for table with ID: {table_id}")
            
            # Initialize match_links set
            match_links = set()  # Use set to avoid duplicates
            
            # Wait for table to load
            try:
                await self.page.wait_for_selector(table_selector, timeout=10000)
                logger.info(f"Found fixtures table: {table_id}")
                
                # Extract all match URLs from the fixtures table
                # Look for links in the score column that point to match reports
                links = await self.page.query_selector_all(f"{table_selector} a[href*='/en/matches/']")
                
                for link in links:
                    href = await link.get_attribute("href")
                    if href and "/en/matches/" in href and len(href.split("/")) > 5:
                        # Convert relative URLs to absolute
                        if href.startswith("/"):
                            href = f"https://fbref.com{href}"
                        match_links.add(href)
                        logger.info(f"Found match URL from table: {href}")
                
            except Exception as e:
                logger.warning(f"Table with ID {table_id} not found: {e}")
                logger.info("Trying alternative approach - looking for match links throughout page")
                
                # Alternative approach: look for any links to match reports on the page
                # This handles completed seasons that may have different page structures
                links = await self.page.query_selector_all("a[href*='/en/matches/']")
                
                for link in links:
                    href = await link.get_attribute("href")
                    link_text = await link.text_content()
                    
                    if href and "/en/matches/" in href and len(href.split("/")) > 5:
                        # Filter out non-match links by checking text content
                        if link_text and ("Match Report" in link_text or "–" in link_text or "-" in link_text):
                            # Convert relative URLs to absolute
                            if href.startswith("/"):
                                href = f"https://fbref.com{href}"
                            match_links.add(href)
                            logger.info(f"Found match URL (alternative): {href}")
            
            match_links_list = list(match_links)
            logger.info(f"Total match URLs found for season {season}: {len(match_links_list)}")
            
            # For completed seasons, we should expect ~380 matches for Premier League
            if len(match_links_list) > 0:
                logger.info(f"Successfully extracted {len(match_links_list)} match URLs")
                return match_links_list
            else:
                logger.error(f"No match URLs found for season {season}")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting season fixtures for {season}: {e}")
            return []
    
    async def extract_match_metadata(self, match_url: str) -> Dict[str, Any]:
        """Extract basic match metadata from individual match page"""
        metadata = {}
        
        try:
            await self.page.goto(match_url)
            await self.page.wait_for_timeout(2000)
            
            # Extract team names and score from the scorebox
            scorebox = await self.page.query_selector("div.scorebox")
            if scorebox:
                # Get team names
                team_elements = await scorebox.query_selector_all("div[itemprop='name']")
                if len(team_elements) >= 2:
                    metadata["home_team"] = (await team_elements[0].text_content()).strip()
                    metadata["away_team"] = (await team_elements[1].text_content()).strip()
                else:
                    # Try alternative approach for team names
                    team_elements = await scorebox.query_selector_all("a[itemprop='name']")
                    if len(team_elements) >= 2:
                        metadata["home_team"] = (await team_elements[0].text_content()).strip()
                        metadata["away_team"] = (await team_elements[1].text_content()).strip()
                    else:
                        # Try another approach - look for team names in the title
                        title = await self.page.title()
                        title_match = re.search(r"(.+?)\s+vs\.\s+(.+?)\s+Match Report", title)
                        if title_match:
                            metadata["home_team"] = title_match.group(1).strip()
                            metadata["away_team"] = title_match.group(2).strip()
                
                # Get scores
                score_elements = await scorebox.query_selector_all("div.score")
                if len(score_elements) >= 2:
                    home_score_text = (await score_elements[0].text_content()).strip()
                    away_score_text = (await score_elements[1].text_content()).strip()
                    metadata["home_score"] = int(home_score_text) if home_score_text.isdigit() else 0
                    metadata["away_score"] = int(away_score_text) if away_score_text.isdigit() else 0
            
            # Extract match date
            date_element = await self.page.query_selector("span.venuetime")
            if date_element:
                date_value = await date_element.get_attribute("data-venue-date")
                if date_value:
                    metadata["match_date"] = date_value
                    
            # Extract referee and venue information
            info_box = await self.page.query_selector("div#info_box, div.info_box, div#meta")
            if info_box:
                info_text = await info_box.text_content()
                
                # Extract referee
                referee_match = re.search(r"Referee:\s*([^,\n]+)", info_text)
                if referee_match:
                    metadata["referee"] = referee_match.group(1).strip()
                
                # Extract assistants
                assistant_match = re.search(r"Assistant(?:s)?:\s*([^,\n]+)", info_text)
                if assistant_match:
                    assistants = [a.strip() for a in assistant_match.group(1).split(",")]
                    metadata["assistant_referees"] = assistants
                
                # Extract 4th official
                fourth_match = re.search(r"Fourth [Oo]fficial:\s*([^,\n]+)", info_text)
                if fourth_match:
                    metadata["fourth_official"] = fourth_match.group(1).strip()
                
                # Extract VAR
                var_match = re.search(r"VAR:\s*([^,\n]+)", info_text)
                if var_match:
                    metadata["var_referee"] = var_match.group(1).strip()
                    
                # Extract stadium
                stadium_match = re.search(r"Venue:\s*([^,\n]+)", info_text)
                if stadium_match:
                    metadata["stadium"] = stadium_match.group(1).strip()
            else:
                # Try to extract information from the page content
                page_text = await self.page.content()
                
                # Extract referee
                referee_match = re.search(r"Referee:\s*([^,\n<]+)", page_text)
                if referee_match:
                    metadata["referee"] = referee_match.group(1).strip()
                
                # Extract stadium
                stadium_match = re.search(r"Venue:\s*([^,\n<]+)", page_text)
                if stadium_match:
                    metadata["stadium"] = stadium_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {match_url}: {e}")
        
        return metadata
    
    async def extract_team_stats(self, team_name: str) -> Dict[str, Any]:
        """Extract statistics for a specific team from current page"""
        stats = {}
        
        try:
            # Look for team stats in various possible table structures
            tables = await self.page.query_selector_all("table")
            
            for table in tables:
                table_text = await table.text_content()
                
                if team_name.lower() in table_text.lower():
                    # Extract possession
                    poss_cell = await table.query_selector("td[data-stat='possession']")
                    if poss_cell:
                        poss_text = (await poss_cell.text_content()).strip().replace("%", "")
                        try:
                            stats["possession"] = float(poss_text)
                        except ValueError:
                            stats["possession"] = 0.0
                    
                    # Extract shots data
                    shots_cell = await table.query_selector("td[data-stat='shots_total']")
                    if shots_cell:
                        try:
                            shots_text = (await shots_cell.text_content()).strip()
                            stats["shots"] = int(shots_text) if shots_text.isdigit() else 0
                        except ValueError:
                            pass
                    
                    # Extract shots on target
                    sot_cell = await table.query_selector("td[data-stat='shots_on_target']")
                    if sot_cell:
                        try:
                            sot_text = (await sot_cell.text_content()).strip()
                            stats["shots_on_target"] = int(sot_text) if sot_text.isdigit() else 0
                        except ValueError:
                            pass
                    
                    # Extract xG
                    xg_cell = await table.query_selector("td[data-stat='xg']")
                    if xg_cell:
                        try:
                            xg_text = (await xg_cell.text_content()).strip()
                            stats["expected_goals"] = float(xg_text) if xg_text else 0.0
                        except ValueError:
                            pass
                    
                    # Extract fouls
                    fouls_cell = await table.query_selector("td[data-stat='fouls']")
                    if fouls_cell:
                        try:
                            fouls_text = (await fouls_cell.text_content()).strip()
                            stats["fouls_committed"] = int(fouls_text) if fouls_text.isdigit() else 0
                        except ValueError:
                            pass
                    
                    # Extract cards
                    yellow_cell = await table.query_selector("td[data-stat='cards_yellow']")
                    if yellow_cell:
                        try:
                            yellow_text = (await yellow_cell.text_content()).strip()
                            stats["yellow_cards"] = int(yellow_text) if yellow_text.isdigit() else 0
                        except ValueError:
                            pass
                    
                    red_cell = await table.query_selector("td[data-stat='cards_red']")
                    if red_cell:
                        try:
                            red_text = (await red_cell.text_content()).strip()
                            stats["red_cards"] = int(red_text) if red_text.isdigit() else 0
                        except ValueError:
                            pass
            
        except Exception as e:
            logger.error(f"Error extracting stats for {team_name}: {e}")
        
        return stats
    
    async def scrape_match_report(self, match_url: str, season: str) -> Optional[MatchData]:
        """Scrape a single match report using the new approach"""
        try:
            logger.info(f"Scraping match: {match_url}")
            
            # Extract metadata (including team names from match page)
            metadata = await self.extract_match_metadata(match_url)
            
            if not metadata.get("home_team") or not metadata.get("away_team"):
                logger.warning(f"Could not extract team names from {match_url}")
                return None
            
            # Extract team stats
            home_stats = await self.extract_team_stats(metadata["home_team"])
            away_stats = await self.extract_team_stats(metadata["away_team"])
            
            # Create MatchData object
            match_data = MatchData(
                season=season,
                match_url=match_url,
                home_team=metadata.get("home_team", ""),
                away_team=metadata.get("away_team", ""),
                home_score=metadata.get("home_score", 0),
                away_score=metadata.get("away_score", 0),
                match_date=metadata.get("match_date", ""),
                stadium=metadata.get("stadium", ""),
                referee=metadata.get("referee", ""),
                assistant_referees=metadata.get("assistant_referees", []),
                fourth_official=metadata.get("fourth_official", ""),
                var_referee=metadata.get("var_referee", ""),
                
                # Home team stats
                home_possession=home_stats.get("possession", 0.0),
                home_shots=home_stats.get("shots", 0),
                home_shots_on_target=home_stats.get("shots_on_target", 0),
                home_expected_goals=home_stats.get("expected_goals", 0.0),
                home_fouls_committed=home_stats.get("fouls_committed", 0),
                home_yellow_cards=home_stats.get("yellow_cards", 0),
                home_red_cards=home_stats.get("red_cards", 0),
                
                # Away team stats
                away_possession=away_stats.get("possession", 0.0),
                away_shots=away_stats.get("shots", 0),
                away_shots_on_target=away_stats.get("shots_on_target", 0),
                away_expected_goals=away_stats.get("expected_goals", 0.0),
                away_fouls_committed=away_stats.get("fouls_committed", 0),
                away_yellow_cards=away_stats.get("yellow_cards", 0),
                away_red_cards=away_stats.get("red_cards", 0),
            )
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error scraping match {match_url}: {e}")
            return None
    
    async def cleanup(self):
        """Clean up the browser"""
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None

# Global scraper instance
scraper = FBrefScraper()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "FBref Match Report Scraper API - Updated with New Approach"}

@api_router.post("/scrape-season/{season}")
async def start_scraping(season: str, background_tasks: BackgroundTasks):
    """Start scraping a season's match reports using the new approach"""
    try:
        # Create scraping status
        status = ScrapingStatus(
            status="running",
            current_match=f"Starting scrape for season {season}"
        )
        
        # Save status to database
        await db.scraping_status.insert_one(status.dict())
        
        # Start background scraping task
        background_tasks.add_task(scrape_season_background, season, status.id)
        
        return {"message": f"Started scraping season {season}", "status_id": status.id}
        
    except Exception as e:
        logger.error(f"Error starting scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def scrape_season_background(season: str, status_id: str):
    """Background task to scrape all matches in a season using new approach"""
    try:
        # Setup browser
        if not await scraper.setup_browser():
            await db.scraping_status.update_one(
                {"id": status_id},
                {"$set": {"status": "failed", "errors": ["Failed to setup browser"]}}
            )
            return
        
        # Get match URLs using new approach
        match_urls = await scraper.extract_season_fixtures(season)
        
        if not match_urls:
            await db.scraping_status.update_one(
                {"id": status_id},
                {"$set": {"status": "failed", "errors": ["No match URLs found"]}}
            )
            return
        
        # Update total matches
        await db.scraping_status.update_one(
            {"id": status_id},
            {"$set": {"total_matches": len(match_urls)}}
        )
        
        # Scrape each match
        scraped_count = 0
        errors = []
        
        for match_url in match_urls:
            try:
                # Update current match
                await db.scraping_status.update_one(
                    {"id": status_id},
                    {"$set": {"current_match": match_url}}
                )
                
                # Scrape match using new approach
                match_data = await scraper.scrape_match_report(match_url, season)
                
                if match_data:
                    # Save to database
                    await db.matches.insert_one(match_data.dict())
                    scraped_count += 1
                    
                    # Update progress
                    await db.scraping_status.update_one(
                        {"id": status_id},
                        {"$set": {"matches_scraped": scraped_count}}
                    )
                else:
                    errors.append(f"Failed to scrape {match_url}")
                
                # Rate limiting - 1 second delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Error scraping {match_url}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Mark as completed
        await db.scraping_status.update_one(
            {"id": status_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "errors": errors
            }}
        )
        
        logger.info(f"Completed scraping season {season}. Scraped {scraped_count} matches with {len(errors)} errors")
        
    except Exception as e:
        logger.error(f"Background scraping error: {e}")
        await db.scraping_status.update_one(
            {"id": status_id},
            {"$set": {"status": "failed", "errors": [str(e)]}}
        )
    finally:
        await scraper.cleanup()

@api_router.get("/scraping-status/{status_id}")
async def get_scraping_status(status_id: str):
    """Get scraping status by ID"""
    status = await db.scraping_status.find_one({"id": status_id}, {"_id": 0})
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return status

@api_router.get("/matches")
async def get_matches(season: Optional[str] = None, team: Optional[str] = None):
    """Get scraped matches with optional filtering"""
    query = {}
    
    if season:
        query["season"] = season
    
    if team:
        query["$or"] = [
            {"home_team": {"$regex": team, "$options": "i"}},
            {"away_team": {"$regex": team, "$options": "i"}}
        ]
    
    matches = await db.matches.find(query, {"_id": 0}).to_list(1000)
    return matches

@api_router.post("/export-csv")
async def export_csv(filters: FilterRequest):
    """Export filtered match data as CSV"""
    try:
        # Build query
        query = {}
        if filters.season:
            query["season"] = filters.season
        
        if filters.teams:
            team_conditions = []
            for team in filters.teams:
                team_conditions.extend([
                    {"home_team": {"$regex": team, "$options": "i"}},
                    {"away_team": {"$regex": team, "$options": "i"}}
                ])
            if team_conditions:
                query["$or"] = team_conditions
        
        if filters.referee:
            query["referee"] = {"$regex": filters.referee, "$options": "i"}
        
        # Get matches
        matches = await db.matches.find(query, {"_id": 0}).to_list(10000)
        
        if not matches:
            raise HTTPException(status_code=404, detail="No matches found with given filters")
        
        # Convert to DataFrame
        df = pd.DataFrame([{k: v for k, v in match.items() if k != "_id"} for match in matches])
        
        # Create CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_data = output.getvalue()
        output.close()
        
        # Return as streaming response
        def generate():
            yield csv_data
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=fbref_matches.csv"}
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/seasons")
async def get_available_seasons():
    """Get list of available seasons"""
    try:
        seasons = await db.matches.distinct("season")
        return {"seasons": sorted(seasons, reverse=True)}
    except Exception as e:
        logger.error(f"Error getting seasons: {e}")
        return {"seasons": ["2023-24"]}  # Default fallback

@api_router.get("/teams")
async def get_available_teams():
    """Get list of available teams"""
    try:
        home_teams = await db.matches.distinct("home_team")
        away_teams = await db.matches.distinct("away_team")
        teams = list(set(home_teams + away_teams))
        return {"teams": sorted(teams)}
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        return {"teams": []}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    await scraper.cleanup()