from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Request
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
    suggestions: List[str] = []
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
        IMPROVED APPROACH: Handle HTML comments and use multiple extraction methods.
        """
        try:
            fixtures_url = self.get_season_fixtures_url(season)
            logger.info(f"Fetching fixtures from: {fixtures_url}")
            
            await self.page.goto(fixtures_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            # Convert season format: 2023-24 -> 2023-2024
            if len(season.split('-')[1]) == 2:  # e.g., "2023-24"
                year_start = season.split('-')[0]
                year_end = "20" + season.split('-')[1]
                season_full = f"{year_start}-{year_end}"
            else:  # Already full format e.g., "2023-2024"
                season_full = season
            
            # Initialize match_links set
            match_links = set()  # Use set to avoid duplicates
            
            # Method 1: Try to extract from HTML content directly (handles commented tables)
            try:
                html_content = await self.page.content()
                
                # Remove HTML comments that may hide the table
                html_content = html_content.replace('<!--', '').replace('-->', '')
                
                # Use regex to find match URLs in the HTML
                import re
                match_url_pattern = r'href=["\']([^"\']*\/en\/matches\/[^"\']*)["\']'
                matches = re.findall(match_url_pattern, html_content)
                
                for match_url in matches:
                    if "/en/matches/" in match_url and len(match_url.split("/")) > 5:
                        # Convert relative URLs to absolute
                        if match_url.startswith("/"):
                            match_url = f"https://fbref.com{match_url}"
                        match_links.add(match_url)
                
                logger.info(f"Found {len(match_links)} match URLs from HTML content analysis")
                
            except Exception as e:
                logger.warning(f"HTML content analysis failed: {e}")
            
            # Method 2: Try finding the fixtures table (original approach)
            if len(match_links) == 0:
                try:
                    table_id = f"sched_{season_full}_9_1"
                    table_selector = f"table#{table_id}"
                    
                    logger.info(f"Looking for table with ID: {table_id}")
                    
                    await self.page.wait_for_selector(table_selector, timeout=10000)
                    logger.info(f"Found fixtures table: {table_id}")
                    
                    # Extract all match URLs from the fixtures table
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
            
            # Method 3: Look for match links throughout the page
            if len(match_links) == 0:
                try:
                    logger.info("Trying alternative approach - looking for match links throughout page")
                    
                    links = await self.page.query_selector_all("a[href*='/en/matches/']")
                    
                    for link in links:
                        href = await link.get_attribute("href")
                        link_text = await link.text_content()
                        
                        if href and "/en/matches/" in href and len(href.split("/")) > 5:
                            # Filter out non-match links by checking text content
                            if link_text and ("Match Report" in link_text or "–" in link_text or "-" in link_text or any(c.isdigit() for c in link_text)):
                                # Convert relative URLs to absolute
                                if href.startswith("/"):
                                    href = f"https://fbref.com{href}"
                                match_links.add(href)
                                logger.info(f"Found match URL (alternative): {href}")
                        
                except Exception as e:
                    logger.warning(f"Alternative approach failed: {e}")
            
            # Method 4: Try using requests library for commented tables
            if len(match_links) == 0:
                try:
                    logger.info("Trying requests-based approach for commented tables")
                    import requests
                    from bs4 import BeautifulSoup
                    
                    response = requests.get(fixtures_url, headers={
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
                    })
                    
                    if response.status_code == 200:
                        # Remove HTML comments
                        html_content = response.text.replace('<!--', '').replace('-->', '')
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Find all links to match reports
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link.get('href')
                            if href and '/en/matches/' in href and len(href.split('/')) > 5:
                                if href.startswith('/'):
                                    href = f"https://fbref.com{href}"
                                match_links.add(href)
                        
                        logger.info(f"Found {len(match_links)} match URLs using requests approach")
                    
                except Exception as e:
                    logger.warning(f"Requests-based approach failed: {e}")
            
            match_links_list = list(match_links)
            logger.info(f"Total match URLs found for season {season}: {len(match_links_list)}")
            
            # For testing, limit to first 20 matches to avoid overwhelming the system
            if len(match_links_list) > 20:
                match_links_list = match_links_list[:20]
                logger.info(f"Limited to first 20 matches for testing: {len(match_links_list)}")
            
            if len(match_links_list) > 0:
                logger.info(f"Successfully extracted {len(match_links_list)} match URLs")
                # Log first few URLs for debugging
                for i, url in enumerate(match_links_list[:3]):
                    logger.info(f"Sample URL {i+1}: {url}")
                return match_links_list
            else:
                logger.error(f"No match URLs found for season {season}")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting season fixtures for {season}: {e}")
            return []
            
    async def extract_season_fixtures_custom(self, season: str, custom_url: str) -> List[str]:
        """
        Extract match URLs from a custom fixtures URL provided by the user.
        """
        try:
            logger.info(f"Using custom fixtures URL: {custom_url}")
            
            await self.page.goto(custom_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            # Initialize match_links set
            match_links = set()
            
            # Method 1: Try HTML content analysis with comment removal
            try:
                html_content = await self.page.content()
                html_content = html_content.replace('<!--', '').replace('-->', '')
                
                import re
                match_url_pattern = r'href=["\']([^"\']*\/en\/matches\/[^"\']*)["\']'
                matches = re.findall(match_url_pattern, html_content)
                
                for match_url in matches:
                    if "/en/matches/" in match_url and len(match_url.split("/")) > 5:
                        if match_url.startswith("/"):
                            match_url = f"https://fbref.com{match_url}"
                        match_links.add(match_url)
                
                logger.info(f"Found {len(match_links)} match URLs from custom URL HTML analysis")
                
            except Exception as e:
                logger.warning(f"HTML analysis on custom URL failed: {e}")
            
            # Method 2: Look for match links throughout the page
            if len(match_links) == 0:
                try:
                    links = await self.page.query_selector_all("a[href*='/en/matches/']")
                    
                    for link in links:
                        href = await link.get_attribute("href")
                        link_text = await link.text_content()
                        
                        if href and "/en/matches/" in href and len(href.split("/")) > 5:
                            if link_text and ("Match Report" in link_text or "–" in link_text or "-" in link_text or any(c.isdigit() for c in link_text)):
                                if href.startswith("/"):
                                    href = f"https://fbref.com{href}"
                                match_links.add(href)
                    
                    logger.info(f"Found {len(match_links)} match URLs from custom URL page scan")
                    
                except Exception as e:
                    logger.warning(f"Page scan on custom URL failed: {e}")
            
            # Method 3: Try requests approach
            if len(match_links) == 0:
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    
                    response = requests.get(custom_url, headers={
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
                    })
                    
                    if response.status_code == 200:
                        html_content = response.text.replace('<!--', '').replace('-->', '')
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link.get('href')
                            if href and '/en/matches/' in href and len(href.split('/')) > 5:
                                if href.startswith('/'):
                                    href = f"https://fbref.com{href}"
                                match_links.add(href)
                        
                        logger.info(f"Found {len(match_links)} match URLs using requests on custom URL")
                    
                except Exception as e:
                    logger.warning(f"Requests approach on custom URL failed: {e}")
            
            match_links_list = list(match_links)
            
            # Limit for testing
            if len(match_links_list) > 20:
                match_links_list = match_links_list[:20]
                logger.info(f"Limited to first 20 matches for testing: {len(match_links_list)}")
            
            if len(match_links_list) > 0:
                logger.info(f"Successfully extracted {len(match_links_list)} match URLs from custom URL")
                # Log first few URLs for debugging
                for i, url in enumerate(match_links_list[:3]):
                    logger.info(f"Sample URL {i+1}: {url}")
                return match_links_list
            else:
                logger.error(f"No match URLs found in custom URL: {custom_url}")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting fixtures from custom URL {custom_url}: {e}")
            return []
    
    async def extract_all_match_data(self, match_url: str, season: str) -> Dict[str, Any]:
        """Extract ALL available data from a match report page"""
        try:
            logger.info(f"Extracting all data from: {match_url}")
            
            await self.page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(3000)
            
            # Initialize comprehensive data structure
            match_data = {
                'basic_info': {},
                'all_tables': {},
                'all_divs_with_data': {},
                'metadata': {
                    'match_url': match_url,
                    'season': season,
                    'extraction_timestamp': datetime.utcnow().isoformat(),
                    'page_title': await self.page.title(),
                    'total_tables_found': 0,
                    'total_data_points': 0
                }
            }
            
            # Extract basic match information first
            match_data['basic_info'] = await self.extract_basic_match_info()
            
            # Extract ALL tables with complete structure
            match_data['all_tables'] = await self.extract_all_tables_comprehensive()
            
            # Extract any other elements that might contain data
            match_data['all_divs_with_data'] = await self.extract_data_elements()
            
            # Update metadata
            match_data['metadata']['total_tables_found'] = len(match_data['all_tables'])
            match_data['metadata']['total_data_points'] = self.count_total_data_points(match_data)
            
            logger.info(f"Extracted {match_data['metadata']['total_tables_found']} tables with {match_data['metadata']['total_data_points']} data points")
            
            return match_data
            
        except Exception as e:
            logger.error(f"Error extracting all data from {match_url}: {e}")
            return {}

    async def extract_all_tables_comprehensive(self) -> Dict[str, Any]:
        """Extract every single table on the page with complete metadata"""
        
        all_tables = {}
        
        try:
            # Find ALL tables on the page
            tables = await self.page.query_selector_all("table")
            
            for i, table in enumerate(tables):
                table_key = f"table_{i}"
                
                # Extract comprehensive table information
                table_data = {
                    'table_metadata': {},
                    'headers': [],
                    'rows': [],
                    'all_cells_raw': [],
                    'data_stat_mapping': {},
                    'table_text_content': ''
                }
                
                # Get table metadata
                table_data['table_metadata'] = await self.extract_table_metadata(table, i)
                
                # Get table text content for reference
                table_data['table_text_content'] = await table.text_content()
                
                # Extract headers with all attributes
                table_data['headers'] = await self.extract_table_headers(table)
                
                # Extract all rows with complete data
                table_data['rows'] = await self.extract_table_rows(table)
                
                # Extract all cells as raw data
                table_data['all_cells_raw'] = await self.extract_all_cells_raw(table)
                
                # Create data-stat mapping
                table_data['data_stat_mapping'] = await self.create_data_stat_mapping(table)
                
                # Add table to collection
                all_tables[table_key] = table_data
                
                # Log table summary
                logger.info(f"Table {i}: ID='{table_data['table_metadata']['id']}', "
                           f"Rows={len(table_data['rows'])}, "
                           f"Headers={len(table_data['headers'])}")
                
        except Exception as e:
            logger.error(f"Error extracting all tables: {e}")
        
        return all_tables

    async def extract_table_metadata(self, table, index: int) -> Dict[str, Any]:
        """Extract all metadata about a table"""
        
        metadata = {
            'index': index,
            'id': '',
            'class': '',
            'data_attributes': {},
            'parent_info': {},
            'all_attributes': {}
        }
        
        try:
            # Basic attributes
            metadata['id'] = await table.get_attribute("id") or f"no_id_{index}"
            metadata['class'] = await table.get_attribute("class") or ""
            
            # All data-* attributes
            for attr_name in ['data-stat', 'data-table', 'data-type']:
                attr_value = await table.get_attribute(attr_name)
                if attr_value:
                    metadata['data_attributes'][attr_name] = attr_value
            
            # Get all attributes
            all_attrs = await table.evaluate("element => Array.from(element.attributes).map(attr => ({name: attr.name, value: attr.value}))")
            metadata['all_attributes'] = all_attrs
            
            # Parent container information
            try:
                parent_tag = await table.evaluate("element => element.parentElement ? element.parentElement.tagName : null")
                parent_id = await table.evaluate("element => element.parentElement ? element.parentElement.id : null")
                parent_class = await table.evaluate("element => element.parentElement ? element.parentElement.className : null")
                metadata['parent_info'] = {
                    'tag': parent_tag,
                    'id': parent_id,
                    'class': parent_class
                }
            except:
                pass
            
        except Exception as e:
            logger.warning(f"Error extracting table metadata: {e}")
        
        return metadata

    async def extract_table_headers(self, table) -> List[Dict[str, Any]]:
        """Extract all header information with complete attributes"""
        
        headers = []
        
        try:
            # Look for headers in thead and tbody
            header_selectors = ["thead tr th", "thead tr td", "tbody tr:first-child th"]
            
            for selector in header_selectors:
                header_elements = await table.query_selector_all(selector)
                if header_elements:
                    for i, header in enumerate(header_elements):
                        header_data = {
                            'index': i,
                            'text': '',
                            'data_stat': '',
                            'title': '',
                            'colspan': 1,
                            'rowspan': 1,
                            'all_attributes': {}
                        }
                        
                        # Extract text
                        header_data['text'] = (await header.text_content()).strip()
                        
                        # Extract key attributes
                        header_data['data_stat'] = await header.get_attribute("data-stat") or ""
                        header_data['title'] = await header.get_attribute("title") or ""
                        
                        # Extract span information
                        colspan = await header.get_attribute("colspan")
                        rowspan = await header.get_attribute("rowspan")
                        header_data['colspan'] = int(colspan) if colspan else 1
                        header_data['rowspan'] = int(rowspan) if rowspan else 1
                        
                        # Get all attributes
                        all_attrs = await header.evaluate("element => Array.from(element.attributes).map(attr => ({name: attr.name, value: attr.value}))")
                        header_data['all_attributes'] = all_attrs
                        
                        headers.append(header_data)
                    break  # Use first successful selector
                    
        except Exception as e:
            logger.warning(f"Error extracting table headers: {e}")
        
        return headers

    async def extract_table_rows(self, table) -> List[Dict[str, Any]]:
        """Extract all row data with complete cell information"""
        
        rows = []
        
        try:
            # Get all rows from tbody
            row_elements = await table.query_selector_all("tbody tr")
            
            for row_index, row in enumerate(row_elements):
                row_data = {
                    'row_index': row_index,
                    'row_text': '',
                    'cells': [],
                    'data_stat_values': {},
                    'row_attributes': {}
                }
                
                # Get row text
                row_data['row_text'] = (await row.text_content()).strip()
                
                # Get row attributes
                row_id = await row.get_attribute("id")
                row_class = await row.get_attribute("class")
                if row_id:
                    row_data['row_attributes']['id'] = row_id
                if row_class:
                    row_data['row_attributes']['class'] = row_class
                
                # Extract all cells
                cells = await row.query_selector_all("td, th")
                
                for cell_index, cell in enumerate(cells):
                    cell_data = {
                        'cell_index': cell_index,
                        'text': '',
                        'data_stat': '',
                        'tag_name': '',
                        'all_attributes': {},
                        'inner_html': '',
                        'has_links': False,
                        'links': []
                    }
                    
                    # Basic cell information
                    cell_data['text'] = (await cell.text_content()).strip()
                    cell_data['data_stat'] = await cell.get_attribute("data-stat") or ""
                    cell_data['tag_name'] = await cell.evaluate("element => element.tagName")
                    
                    # Get inner HTML for complex content
                    cell_data['inner_html'] = await cell.inner_html()
                    
                    # Check for links
                    links = await cell.query_selector_all("a")
                    if links:
                        cell_data['has_links'] = True
                        for link in links:
                            link_href = await link.get_attribute("href")
                            link_text = await link.text_content()
                            cell_data['links'].append({
                                'href': link_href,
                                'text': link_text.strip()
                            })
                    
                    # Get all attributes
                    all_attrs = await cell.evaluate("element => Array.from(element.attributes).map(attr => ({name: attr.name, value: attr.value}))")
                    cell_data['all_attributes'] = all_attrs
                    
                    # Store in row
                    row_data['cells'].append(cell_data)
                    
                    # Also store by data-stat for easy access
                    if cell_data['data_stat']:
                        row_data['data_stat_values'][cell_data['data_stat']] = cell_data['text']
                
                rows.append(row_data)
                
        except Exception as e:
            logger.warning(f"Error extracting table rows: {e}")
        
        return rows

    async def extract_all_cells_raw(self, table) -> List[Dict[str, Any]]:
        """Extract every single cell as raw data for complete coverage"""
        
        all_cells = []
        
        try:
            cells = await table.query_selector_all("td, th")
            
            for i, cell in enumerate(cells):
                cell_info = {
                    'global_index': i,
                    'text_content': (await cell.text_content()).strip(),
                    'inner_html': await cell.inner_html(),
                    'tag_name': await cell.evaluate("element => element.tagName"),
                    'data_stat': await cell.get_attribute("data-stat"),
                    'class': await cell.get_attribute("class"),
                    'id': await cell.get_attribute("id"),
                    'title': await cell.get_attribute("title")
                }
                
                # Get all attributes safely
                try:
                    all_attrs = await cell.evaluate("element => Array.from(element.attributes).map(attr => ({name: attr.name, value: attr.value}))")
                    cell_info['all_attributes'] = all_attrs
                except:
                    cell_info['all_attributes'] = []
                
                all_cells.append(cell_info)
                
        except Exception as e:
            logger.warning(f"Error extracting raw cells: {e}")
        
        return all_cells

    async def create_data_stat_mapping(self, table) -> Dict[str, str]:
        """Create a mapping of all data-stat attributes to their values"""
        
        mapping = {}
        
        try:
            cells_with_data_stat = await table.query_selector_all("[data-stat]")
            
            for cell in cells_with_data_stat:
                data_stat = await cell.get_attribute("data-stat")
                text_value = (await cell.text_content()).strip()
                
                if data_stat and text_value:
                    # Handle multiple values for same data-stat (use list)
                    if data_stat in mapping:
                        if isinstance(mapping[data_stat], list):
                            mapping[data_stat].append(text_value)
                        else:
                            mapping[data_stat] = [mapping[data_stat], text_value]
                    else:
                        mapping[data_stat] = text_value
                        
        except Exception as e:
            logger.warning(f"Error creating data-stat mapping: {e}")
        
        return mapping

    async def extract_basic_match_info(self) -> Dict[str, Any]:
        """Extract basic match information"""
        
        basic_info = {
            'page_title': '',
            'scorebox_data': {},
            'match_info_box': {},
            'breadcrumb_info': {}
        }
        
        try:
            # Page title
            basic_info['page_title'] = await self.page.title()
            
            # Scorebox information
            scorebox = await self.page.query_selector("div.scorebox")
            if scorebox:
                basic_info['scorebox_data'] = {
                    'full_html': await scorebox.inner_html(),
                    'text_content': await scorebox.text_content(),
                    'all_elements': []
                }
                
                # Extract all elements in scorebox
                elements = await scorebox.query_selector_all("*")
                for element in elements:
                    element_info = {
                        'tag': await element.evaluate("element => element.tagName"),
                        'text': (await element.text_content()).strip(),
                        'class': await element.get_attribute("class"),
                        'id': await element.get_attribute("id"),
                        'itemprop': await element.get_attribute("itemprop"),
                        'data_stat': await element.get_attribute("data-stat")
                    }
                    basic_info['scorebox_data']['all_elements'].append(element_info)
            
            # Match info box
            info_selectors = ["div.info", "div#info", "div.meta", "div#meta", "div[class*='info']"]
            for selector in info_selectors:
                info_boxes = await self.page.query_selector_all(selector)
                for i, info_box in enumerate(info_boxes):
                    key = f'{selector.replace("div.", "").replace("#", "").replace("[", "").replace("]", "")}_{i}'
                    basic_info['match_info_box'][key] = {
                        'html': await info_box.inner_html(),
                        'text': await info_box.text_content()
                    }
            
            # Breadcrumb/navigation info
            breadcrumb_selectors = ["div.breadcrumb", "nav.breadcrumb", ".breadcrumb"]
            for selector in breadcrumb_selectors:
                breadcrumbs = await self.page.query_selector_all(selector)
                for i, breadcrumb in enumerate(breadcrumbs):
                    basic_info['breadcrumb_info'][f'breadcrumb_{i}'] = await breadcrumb.text_content()
                
        except Exception as e:
            logger.warning(f"Error extracting basic match info: {e}")
        
        return basic_info

    def count_total_data_points(self, match_data: Dict[str, Any]) -> int:
        """Count total data points extracted"""
        total = 0
        
        try:
            for table_data in match_data.get('all_tables', {}).values():
                total += len(table_data.get('data_stat_mapping', {}))
                total += len(table_data.get('all_cells_raw', []))
            
            total += len(match_data.get('all_divs_with_data', {}))
            
        except Exception:
            pass
        
        return total
    
    async def extract_team_stats(self, team_name: str) -> Dict[str, Any]:
        """Extract statistics for a specific team from current page"""
        stats = {}
        
        try:
            logger.info(f"Extracting stats for team: {team_name}")
            
            # Look for team stats in various possible table structures
            tables = await self.page.query_selector_all("table")
            
            for table in tables:
                table_text = await table.text_content()
                table_id = await table.get_attribute("id") or ""
                
                # Check if this table contains stats for the team
                if team_name.lower() in table_text.lower() or "stats" in table_id.lower():
                    logger.info(f"Found potential stats table: {table_id}")
                    
                    # Extract possession
                    poss_cell = await table.query_selector("td[data-stat='possession']")
                    if poss_cell:
                        poss_text = (await poss_cell.text_content()).strip().replace("%", "")
                        try:
                            stats["possession"] = float(poss_text)
                            logger.info(f"Found possession: {stats['possession']}%")
                        except ValueError:
                            stats["possession"] = 0.0
                    
                    # Extract shots data
                    shots_cell = await table.query_selector("td[data-stat='shots_total']")
                    if shots_cell:
                        try:
                            shots_text = (await shots_cell.text_content()).strip()
                            stats["shots"] = int(shots_text) if shots_text.isdigit() else 0
                            logger.info(f"Found shots: {stats['shots']}")
                        except ValueError:
                            pass
                    
                    # Extract shots on target
                    sot_cell = await table.query_selector("td[data-stat='shots_on_target']")
                    if sot_cell:
                        try:
                            sot_text = (await sot_cell.text_content()).strip()
                            stats["shots_on_target"] = int(sot_text) if sot_text.isdigit() else 0
                            logger.info(f"Found shots on target: {stats['shots_on_target']}")
                        except ValueError:
                            pass
                    
                    # Extract xG
                    xg_cell = await table.query_selector("td[data-stat='xg']")
                    if xg_cell:
                        try:
                            xg_text = (await xg_cell.text_content()).strip()
                            stats["expected_goals"] = float(xg_text) if xg_text else 0.0
                            logger.info(f"Found expected goals: {stats['expected_goals']}")
                        except ValueError:
                            pass
                    
                    # Extract fouls
                    fouls_cell = await table.query_selector("td[data-stat='fouls']")
                    if fouls_cell:
                        try:
                            fouls_text = (await fouls_cell.text_content()).strip()
                            stats["fouls_committed"] = int(fouls_text) if fouls_text.isdigit() else 0
                            logger.info(f"Found fouls committed: {stats['fouls_committed']}")
                        except ValueError:
                            pass
                    
                    # Extract cards
                    yellow_cell = await table.query_selector("td[data-stat='cards_yellow']")
                    if yellow_cell:
                        try:
                            yellow_text = (await yellow_cell.text_content()).strip()
                            stats["yellow_cards"] = int(yellow_text) if yellow_text.isdigit() else 0
                            logger.info(f"Found yellow cards: {stats['yellow_cards']}")
                        except ValueError:
                            pass
                    
                    red_cell = await table.query_selector("td[data-stat='cards_red']")
                    if red_cell:
                        try:
                            red_text = (await red_cell.text_content()).strip()
                            stats["red_cards"] = int(red_text) if red_text.isdigit() else 0
                            logger.info(f"Found red cards: {stats['red_cards']}")
                        except ValueError:
                            pass
                    
                    # If we found at least some stats, we can break
                    if len(stats) > 0:
                        break
            
            # If we didn't find any stats, try a more general approach
            if not stats:
                logger.info("Trying alternative approach for stats extraction")
                
                # Look for any tables with stats in the ID or class
                stats_tables = await self.page.query_selector_all("table[id*='stats'], table[class*='stats']")
                
                for table in stats_tables:
                    table_id = await table.get_attribute("id") or ""
                    logger.info(f"Checking stats table: {table_id}")
                    
                    # Look for rows that might contain team stats
                    rows = await table.query_selector_all("tr")
                    
                    for row in rows:
                        row_text = await row.text_content()
                        
                        # Check if this row contains the team name
                        if team_name.lower() in row_text.lower():
                            logger.info(f"Found row with team name: {team_name}")
                            
                            # Extract cells
                            cells = await row.query_selector_all("td")
                            
                            # Try to identify stats based on position or data attributes
                            for i, cell in enumerate(cells):
                                cell_text = (await cell.text_content()).strip()
                                data_stat = await cell.get_attribute("data-stat") or ""
                                
                                # Use data-stat attribute if available
                                if data_stat:
                                    if "possession" in data_stat and cell_text:
                                        try:
                                            stats["possession"] = float(cell_text.replace("%", ""))
                                        except ValueError:
                                            pass
                                    elif "shots" in data_stat and "target" not in data_stat and cell_text:
                                        try:
                                            stats["shots"] = int(cell_text) if cell_text.isdigit() else 0
                                        except ValueError:
                                            pass
                                    elif "target" in data_stat and cell_text:
                                        try:
                                            stats["shots_on_target"] = int(cell_text) if cell_text.isdigit() else 0
                                        except ValueError:
                                            pass
                                    elif "xg" in data_stat and cell_text:
                                        try:
                                            stats["expected_goals"] = float(cell_text) if cell_text else 0.0
                                        except ValueError:
                                            pass
                                    elif "foul" in data_stat and cell_text:
                                        try:
                                            stats["fouls_committed"] = int(cell_text) if cell_text.isdigit() else 0
                                        except ValueError:
                                            pass
                                    elif "yellow" in data_stat and cell_text:
                                        try:
                                            stats["yellow_cards"] = int(cell_text) if cell_text.isdigit() else 0
                                        except ValueError:
                                            pass
                                    elif "red" in data_stat and cell_text:
                                        try:
                                            stats["red_cards"] = int(cell_text) if cell_text.isdigit() else 0
                                        except ValueError:
                                            pass
                            
                            # If we found at least some stats, we can break
                            if len(stats) > 0:
                                break
                    
                    # If we found at least some stats, we can break
                    if len(stats) > 0:
                        break
            
            # Log the stats we found
            if stats:
                logger.info(f"Stats found for {team_name}: {stats}")
            else:
                logger.warning(f"No stats found for {team_name}")
            
        except Exception as e:
            logger.error(f"Error extracting stats for {team_name}: {e}")
        
        return stats
    
    async def scrape_match_report(self, match_url: str, season: str) -> Optional[MatchData]:
        """Scrape a single match report using the new approach"""
        try:
            logger.info(f"Scraping match: {match_url}")
            
            # Add longer timeout and wait for network idle
            await self.page.goto(match_url, timeout=60000, wait_until="networkidle")
            await self.page.wait_for_timeout(3000)  # Wait longer for page to fully load
            
            # Take a screenshot for debugging
            screenshot_path = f"/tmp/fbref_match_{match_url.split('/')[-2]}.png"
            await self.page.screenshot(path=screenshot_path)
            logger.info(f"Match page screenshot saved to {screenshot_path}")
            
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
            
            logger.info(f"Successfully scraped match: {metadata.get('home_team', '')} vs {metadata.get('away_team', '')}")
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
async def start_scraping(season: str, background_tasks: BackgroundTasks, request: Request):
    """Start scraping a season's match reports using the new approach"""
    try:
        # Handle request body for custom URL
        custom_url = None
        try:
            body = await request.json()
            custom_url = body.get("custom_url")
        except:
            # No body or invalid JSON, that's fine
            pass
        
        # Create scraping status
        status = ScrapingStatus(
            status="running",
            current_match=f"Starting scrape for season {season}" + (f" with custom URL: {custom_url}" if custom_url else "")
        )
        
        # Save status to database
        await db.scraping_status.insert_one(status.dict())
        
        # Start background scraping task
        background_tasks.add_task(scrape_season_background, season, status.id, custom_url)
        
        return {"message": f"Started scraping season {season}", "status_id": status.id}
        
    except Exception as e:
        logger.error(f"Error starting scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def scrape_season_background(season: str, status_id: str, custom_url: Optional[str] = None):
    """Background task to scrape all matches in a season using new approach"""
    try:
        # Setup browser
        if not await scraper.setup_browser():
            await db.scraping_status.update_one(
                {"id": status_id},
                {"$set": {"status": "failed", "errors": ["Failed to setup browser"]}}
            )
            return
        
        # Get match URLs using new approach (with optional custom URL)
        if custom_url:
            # Use custom URL provided by user
            match_urls = await scraper.extract_season_fixtures_custom(season, custom_url)
        else:
            # Use default URL generation
            match_urls = await scraper.extract_season_fixtures(season)
        
        if not match_urls:
            error_msg = f"No match URLs found for season {season}"
            if not custom_url:
                error_msg += ". Try providing a custom fixtures URL."
            
            await db.scraping_status.update_one(
                {"id": status_id},
                {"$set": {
                    "status": "failed", 
                    "errors": [error_msg],
                    "suggestions": [
                        "1. Check if the season format is correct (e.g., '2024-25')",
                        "2. Verify the fixtures page exists on FBref.com",
                        "3. Try using the manual URL option with the correct fixtures page",
                        "4. For historical seasons, the page structure might be different"
                    ]
                }}
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
        match_extraction_errors = []
        
        for i, match_url in enumerate(match_urls):
            try:
                # Update current match
                await db.scraping_status.update_one(
                    {"id": status_id},
                    {"$set": {"current_match": f"Processing match {i+1}/{len(match_urls)}: {match_url}"}}
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
                    match_extraction_errors.append(f"Failed to extract data from: {match_url}")
                
                # Rate limiting - 1 second delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Error scraping {match_url}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Prepare final status
        final_errors = errors + match_extraction_errors
        suggestions = []
        
        if match_extraction_errors:
            suggestions.extend([
                "MATCH EXTRACTION ISSUES DETECTED:",
                "• Some match report pages couldn't be parsed",
                "• This could be due to:",
                "  - Changes in FBref's match report page structure",
                "  - Anti-scraping measures on individual match pages",
                "  - Network timeouts or connection issues",
                f"• Successfully extracted: {scraped_count}/{len(match_urls)} matches",
                "• You can help by:",
                "  - Checking if match report links are valid",
                "  - Inspecting page structure for changes",
                "  - Running with smaller batch sizes"
            ])
        
        if scraped_count == 0:
            suggestions.extend([
                "NO MATCHES EXTRACTED - POSSIBLE CAUSES:",
                "• Match report links may be invalid or redirecting",
                "• FBref may have changed their page structure",
                "• Anti-scraping measures may be blocking requests",
                "• Network connectivity issues",
                "RECOMMENDED ACTIONS:",
                "• Try manual URL with a known working fixtures page",
                "• Check browser logs for specific errors",
                "• Verify match URLs are accessible manually"
            ])
        
        # Mark as completed
        await db.scraping_status.update_one(
            {"id": status_id},
            {"$set": {
                "status": "completed" if scraped_count > 0 else "failed",
                "completed_at": datetime.utcnow(),
                "errors": final_errors,
                "suggestions": suggestions
            }}
        )
        
        logger.info(f"Completed scraping season {season}. Scraped {scraped_count} matches with {len(final_errors)} errors")
        
    except Exception as e:
        logger.error(f"Background scraping error: {e}")
        await db.scraping_status.update_one(
            {"id": status_id},
            {"$set": {
                "status": "failed", 
                "errors": [str(e)],
                "suggestions": [
                    "UNEXPECTED ERROR OCCURRED:",
                    "• Check backend logs for detailed error information",
                    "• Verify browser/Playwright setup is working",
                    "• Try restarting the scraping process"
                ]
            }}
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