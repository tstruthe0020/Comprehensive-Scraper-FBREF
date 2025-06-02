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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
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
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome driver with headless options for ARM64"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Use Electron's ARM64 ChromeDriver
            service = Service("/usr/local/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)
            
            logger.info("ARM64 ChromeDriver setup successful - REAL scraping enabled")
            return True
            
        except Exception as e:
            logger.error(f"ChromeDriver setup failed: {e}")
            return False
    
    def get_season_fixtures_url(self, season: str) -> str:
        """Get the fixtures URL for a specific season"""
        if season == "2024-25":
            return "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
        else:
            return f"https://fbref.com/en/comps/9/{season}/schedule/Premier-League-Scores-and-Fixtures"
    
    def extract_match_links(self, season: str) -> List[str]:
        """Extract all match report links from a season's fixtures page"""
        try:
            fixtures_url = self.get_season_fixtures_url(season)
            logger.info(f"Fetching fixtures from: {fixtures_url}")
            
            self.driver.get(fixtures_url)
            time.sleep(5)
            
            # Find match report links - look for both score links and "Match Report" text
            match_links = set()  # Use set to avoid duplicates
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            import re
            # Score patterns: "2-1", "0-0", etc. (including em dash and regular dash)
            score_pattern = re.compile(r'^\d+[–-]\d+$')
            
            for link in links:
                href = link.get_attribute("href")
                link_text = link.text.strip()
                
                if href and "/en/matches/" in href and len(href.split("/")) > 5:
                    # Check for score links or "Match Report" text
                    if score_pattern.match(link_text) or link_text == "Match Report":
                        match_links.add(href)
                        logger.info(f"Found match: {link_text} -> {href}")
            
            match_links_list = list(match_links)
            logger.info(f"Found {len(match_links_list)} unique match reports for season {season}")
            return match_links_list
            
        except Exception as e:
            logger.error(f"Error extracting match links for season {season}: {e}")
            return []
    
    def extract_match_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract basic match metadata"""
        metadata = {}
        
        try:
            # Extract team names and score from the page title or scorebox
            scorebox = soup.find("div", {"class": "scorebox"})
            if scorebox:
                teams = scorebox.find_all("div", {"itemprop": "name"})
                if len(teams) >= 2:
                    metadata["home_team"] = teams[0].get_text().strip()
                    metadata["away_team"] = teams[1].get_text().strip()
                
                # Extract scores
                scores = scorebox.find_all("div", {"class": "score"})
                if len(scores) >= 2:
                    metadata["home_score"] = int(scores[0].get_text().strip() or 0)
                    metadata["away_score"] = int(scores[1].get_text().strip() or 0)
            
            # Extract match date
            match_date_elem = soup.find("span", {"class": "venuetime"})
            if match_date_elem:
                date_text = match_date_elem.get("data-venue-date")
                if date_text:
                    metadata["match_date"] = date_text
                    
            # Extract referee information
            match_info = soup.find("div", {"id": "info_box"}) or soup.find("div", {"class": "info_box"})
            if match_info:
                referee_text = match_info.get_text()
                
                # Extract referee
                referee_match = re.search(r"Referee:\s*([^,\n]+)", referee_text)
                if referee_match:
                    metadata["referee"] = referee_match.group(1).strip()
                
                # Extract assistants
                assistant_match = re.search(r"Assistant(?:s)?:\s*([^,\n]+)", referee_text)
                if assistant_match:
                    assistants = [a.strip() for a in assistant_match.group(1).split(",")]
                    metadata["assistant_referees"] = assistants
                
                # Extract 4th official
                fourth_match = re.search(r"Fourth [Oo]fficial:\s*([^,\n]+)", referee_text)
                if fourth_match:
                    metadata["fourth_official"] = fourth_match.group(1).strip()
                
                # Extract VAR
                var_match = re.search(r"VAR:\s*([^,\n]+)", referee_text)
                if var_match:
                    metadata["var_referee"] = var_match.group(1).strip()
                    
                # Extract stadium
                stadium_match = re.search(r"Venue:\s*([^,\n]+)", referee_text)
                if stadium_match:
                    metadata["stadium"] = stadium_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    def extract_team_stats(self, soup: BeautifulSoup, team_name: str) -> Dict[str, Any]:
        """Extract statistics for a specific team"""
        stats = {}
        
        try:
            # Normalize team name for table IDs
            team_id = team_name.replace(" ", "-").replace("'", "")
            
            # Summary stats table
            summary_table = soup.find("table", {"id": f"stats_summary_{team_id}"})
            if summary_table:
                # Extract possession from summary
                poss_cell = summary_table.find("td", {"data-stat": "possession"})
                if poss_cell:
                    poss_text = poss_cell.get_text().strip().replace("%", "")
                    try:
                        stats["possession"] = float(poss_text)
                    except ValueError:
                        stats["possession"] = 0.0
            
            # Look for team stats in various possible table structures
            for table in soup.find_all("table"):
                table_text = table.get_text().lower()
                
                if team_name.lower() in table_text:
                    # Extract shots data
                    shots_cell = table.find("td", {"data-stat": "shots_total"})
                    if shots_cell:
                        try:
                            stats["shots"] = int(shots_cell.get_text().strip() or 0)
                        except ValueError:
                            pass
                    
                    # Extract shots on target
                    sot_cell = table.find("td", {"data-stat": "shots_on_target"})
                    if sot_cell:
                        try:
                            stats["shots_on_target"] = int(sot_cell.get_text().strip() or 0)
                        except ValueError:
                            pass
                    
                    # Extract xG
                    xg_cell = table.find("td", {"data-stat": "xg"})
                    if xg_cell:
                        try:
                            stats["expected_goals"] = float(xg_cell.get_text().strip() or 0)
                        except ValueError:
                            pass
                    
                    # Extract fouls
                    fouls_cell = table.find("td", {"data-stat": "fouls"})
                    if fouls_cell:
                        try:
                            stats["fouls_committed"] = int(fouls_cell.get_text().strip() or 0)
                        except ValueError:
                            pass
                    
                    # Extract cards
                    yellow_cell = table.find("td", {"data-stat": "cards_yellow"})
                    if yellow_cell:
                        try:
                            stats["yellow_cards"] = int(yellow_cell.get_text().strip() or 0)
                        except ValueError:
                            pass
                    
                    red_cell = table.find("td", {"data-stat": "cards_red"})
                    if red_cell:
                        try:
                            stats["red_cards"] = int(red_cell.get_text().strip() or 0)
                        except ValueError:
                            pass
            
        except Exception as e:
            logger.error(f"Error extracting stats for {team_name}: {e}")
        
        return stats
    
    def scrape_match_report(self, match_url: str, season: str) -> Optional[MatchData]:
        """Scrape a single match report"""
        try:
            logger.info(f"Scraping match: {match_url}")
            self.driver.get(match_url)
            time.sleep(3)
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract metadata
            metadata = self.extract_match_metadata(soup)
            
            if not metadata.get("home_team") or not metadata.get("away_team"):
                logger.warning(f"Could not extract team names from {match_url}")
                return None
            
            # Extract team stats
            home_stats = self.extract_team_stats(soup, metadata["home_team"])
            away_stats = self.extract_team_stats(soup, metadata["away_team"])
            
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
    
    def cleanup(self):
        """Clean up the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

# Global scraper instance
scraper = FBrefScraper()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "FBref Match Report Scraper API"}

@api_router.post("/scrape-season/{season}")
async def start_scraping(season: str, background_tasks: BackgroundTasks):
    """Start scraping a season's match reports"""
    try:
        # Create scraping status
        status = ScrapingStatus(
            status="running",
            request_type="single_season",
            seasons=[season],
            current_season=season,
            total_seasons=1,
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
    """Background task to scrape all matches in a season"""
    try:
        # Setup driver
        if not scraper.setup_driver():
            await db.scraping_status.update_one(
                {"id": status_id},
                {"$set": {"status": "failed", "errors": ["Failed to setup Chrome driver"]}}
            )
            return
        
        # Get match links
        match_links = scraper.extract_match_links(season)
        
        if not match_links:
            await db.scraping_status.update_one(
                {"id": status_id},
                {"$set": {"status": "failed", "errors": ["No match links found"]}}
            )
            return
        
        # Update total matches
        await db.scraping_status.update_one(
            {"id": status_id},
            {"$set": {
                "total_matches": len(match_links),
                "fixtures_found": len(match_links),
                "current_season": season,
                "seasons": [season],
                "total_seasons": 1
            }}
        )
        
        # Scrape each match
        scraped_count = 0
        errors = []
        
        for match_url in match_links:
            try:
                # Update current match
                await db.scraping_status.update_one(
                    {"id": status_id},
                    {"$set": {"current_match": match_url}}
                )
                
                # Scrape match
                team_match_data_list = scraper.scrape_match_report(match_url, season)
                
                if team_match_data_list:
                    # Save both teams' data to database
                    for team_match_data in team_match_data_list:
                        await db.team_matches.insert_one(team_match_data.dict())
                    scraped_count += 1
                    
                    # Update progress
                    await db.scraping_status.update_one(
                        {"id": status_id},
                        {"$set": {
                            "matches_scraped": scraped_count,
                            "completed_seasons": 1 if scraped_count == len(match_links) else 0
                        }}
                    )
                else:
                    errors.append(f"Failed to scrape {match_url}")
                
                # Small delay between requests
                time.sleep(2)
                
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
                "errors": errors,
                "completed_seasons": 1
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
        scraper.cleanup()

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
        query["team_name"] = {"$regex": team, "$options": "i"}
    
    matches = await db.team_matches.find(query, {"_id": 0}).to_list(1000)
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
                team_conditions.append({"team_name": {"$regex": team, "$options": "i"}})
            if team_conditions:
                query["$or"] = team_conditions
        
        if filters.referee:
            query["referee"] = {"$regex": filters.referee, "$options": "i"}
        
        # Get matches
        matches = await db.team_matches.find(query, {"_id": 0}).to_list(10000)
        
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
            headers={"Content-Disposition": "attachment; filename=fbref_team_matches.csv"}
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/seasons")
async def get_available_seasons():
    """Get list of available seasons"""
    try:
        seasons = await db.team_matches.distinct("season")
        return {"seasons": sorted(seasons, reverse=True)}
    except Exception as e:
        logger.error(f"Error getting seasons: {e}")
        return {"seasons": ["2023-24"]}  # Default fallback

@api_router.get("/teams")
async def get_available_teams():
    """Get list of available teams"""
    try:
        teams = await db.team_matches.distinct("team_name")
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
    scraper.cleanup()
