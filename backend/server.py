from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import re
from bs4 import BeautifulSoup
import csv
import io
import os
from typing import List, Dict
from fastapi.responses import StreamingResponse
from playwright.async_api import async_playwright
import asyncio
from urllib.parse import urlparse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapingRequest(BaseModel):
    urls: List[str]  # Changed from single url to multiple urls

class SeasonResult(BaseModel):
    url: str
    season_name: str
    success: bool
    message: str
    links: List[str] = []

class ScrapingResponse(BaseModel):
    success: bool
    message: str
    seasons: List[SeasonResult] = []
    total_links: int = 0
    csv_data: str = ""

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

async def scrape_fbref_with_playwright(url: str) -> SeasonResult:
    """Scrape a single FBREF fixtures page using Playwright"""
    try:
        # Extract season name from URL for better organization
        season_name = "Unknown Season"
        if "/schedule/" in url:
            parts = url.split("/")
            for i, part in enumerate(parts):
                if "schedule" in part and i > 0:
                    season_name = parts[i-1] if parts[i-1] != "schedule" else "Current Season"
                    break
        
        async with async_playwright() as p:
            # Launch Firefox browser with stealth settings
            browser = await p.firefox.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # Create a new context with realistic browser settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Navigate to the page with realistic timing
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait a bit to let any dynamic content load
            await page.wait_for_timeout(2000)
            
            # Get page content
            content = await page.content()
            
            await browser.close()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the Score column header with multiple fallback strategies
        score_header = None
        
        # Strategy 1: Exact match for the specified attributes
        score_header = soup.find('th', {
            'aria-label': 'Score',
            'data-stat': 'score',
            'scope': 'col'
        })
        
        # Strategy 2: Find by data-stat only
        if not score_header:
            score_header = soup.find('th', {'data-stat': 'score'})
        
        # Strategy 3: Find by text content
        if not score_header:
            score_header = soup.find('th', string=re.compile(r'Score', re.IGNORECASE))
            
        # Strategy 4: Find by aria-label only
        if not score_header:
            score_header = soup.find('th', {'aria-label': re.compile(r'Score', re.IGNORECASE)})
        
        if not score_header:
            return SeasonResult(
                url=url,
                season_name=season_name,
                success=False,
                message="Could not find the Score column in the table. Page structure may be different.",
                links=[]
            )
        
        # Find the table containing the score header
        table = score_header.find_parent('table')
        if not table:
            return SeasonResult(
                url=url,
                season_name=season_name,
                success=False,
                message="Could not find the table containing the Score column.",
                links=[]
            )
        
        # Get column index of Score column
        headers_row = score_header.find_parent('tr')
        headers = headers_row.find_all(['th', 'td'])
        score_column_index = None
        
        for i, header in enumerate(headers):
            if (header.get('data-stat') == 'score' or 
                (header.get('aria-label') and 'score' in header.get('aria-label').lower()) or
                (header.get_text(strip=True).lower() == 'score')):
                score_column_index = i
                break
        
        if score_column_index is None:
            return SeasonResult(
                url=url,
                season_name=season_name,
                success=False,
                message="Could not determine the position of the Score column.",
                links=[]
            )
        
        # Extract match report links from Score column
        match_links = []
        tbody = table.find('tbody')
        
        if tbody:
            rows = tbody.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) > score_column_index:
                    score_cell = cells[score_column_index]
                    # Look for links in the score cell
                    links = score_cell.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        # Check if it's a match report link
                        if '/matches/' in href:
                            full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                            if full_url not in match_links:
                                match_links.append(full_url)
        
        # If no links in score column, try alternative approach
        if not match_links:
            all_links = table.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if '/matches/' in href:
                    full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                    if full_url not in match_links:
                        match_links.append(full_url)
        
        if not match_links:
            return SeasonResult(
                url=url,
                season_name=season_name,
                success=False,
                message="No match report links found. This could mean no completed matches for this season.",
                links=[]
            )
        
        return SeasonResult(
            url=url,
            season_name=season_name,
            success=True,
            message=f"Successfully extracted {len(match_links)} match report links",
            links=match_links
        )
        
    except Exception as e:
        return SeasonResult(
            url=url,
            season_name=season_name,
            success=False,
            message=f"Error scraping {url}: {str(e)}",
            links=[]
        )

@app.post("/api/scrape-fbref")
async def scrape_multiple_fbref_seasons(request: ScrapingRequest):
    """Scrape multiple FBREF fixture pages sequentially"""
    try:
        if not request.urls or len(request.urls) == 0:
            raise HTTPException(status_code=400, detail="Please provide at least one FBREF URL")
        
        # Validate all URLs
        for url in request.urls:
            if not url or not url.strip().startswith("https://fbref.com"):
                raise HTTPException(status_code=400, detail=f"Invalid FBREF URL: {url}")
        
        season_results = []
        all_links = []
        
        # Process each URL sequentially
        for url in request.urls:
            url = url.strip()
            print(f"Processing: {url}")
            result = await scrape_fbref_with_playwright(url)
            season_results.append(result)
            
            if result.success:
                all_links.extend(result.links)
            
            # Small delay between requests to be respectful
            await asyncio.sleep(1)
        
        # Generate CSV content with all compiled data
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Write headers for match data
        csv_writer.writerow([
            'Season', 'Match_Report_URL', 'Home_Team', 'Away_Team', 'Date', 'Score',
            'Home_Goals', 'Away_Goals', 'Competition', 'Venue', 'Source_URL'
        ])
        
        # Write all match links organized by season
        for season_result in season_results:
            if season_result.success:
                for link in season_result.links:
                    csv_writer.writerow([
                        season_result.season_name, link, '', '', '', '', 
                        '', '', '', '', season_result.url
                    ])
        
        # Add separator and player data headers
        csv_writer.writerow([])  # Empty row separator
        csv_writer.writerow(['=== PLAYER DATA ==='])
        csv_writer.writerow([
            'Season', 'Match_URL', 'Player_Name', 'Team', 'Position', 'Minutes_Played',
            'Goals', 'Assists', 'Shots', 'Shots_on_Target', 'Passes_Completed',
            'Pass_Accuracy', 'Tackles', 'Interceptions', 'Fouls', 'Cards'
        ])
        
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()
        
        # Prepare response
        successful_seasons = [s for s in season_results if s.success]
        failed_seasons = [s for s in season_results if not s.success]
        
        if len(successful_seasons) == 0:
            return ScrapingResponse(
                success=False,
                message="Failed to scrape any seasons. All URLs encountered errors.",
                seasons=season_results,
                total_links=0,
                csv_data=""
            )
        
        message_parts = []
        message_parts.append(f"Successfully processed {len(successful_seasons)}/{len(request.urls)} seasons")
        message_parts.append(f"Total match links extracted: {len(all_links)}")
        
        if failed_seasons:
            message_parts.append(f"{len(failed_seasons)} seasons failed")
        
        return ScrapingResponse(
            success=True,
            message=" | ".join(message_parts),
            seasons=season_results,
            total_links=len(all_links),
            csv_data=csv_content
        )
        
    except Exception as e:
        return ScrapingResponse(
            success=False,
            message=f"An error occurred during processing: {str(e)}",
            seasons=[],
            total_links=0,
            csv_data=""
        )

@app.post("/api/demo-scrape")
async def demo_scrape_fbref():
    """Demo endpoint that shows what successful scraping would look like"""
    # Sample match report links that would be extracted
    demo_links = [
        "https://fbref.com/en/matches/cc5b4244/Manchester-United-Fulham-August-16-2024-Premier-League",
        "https://fbref.com/en/matches/8b1e4321/Arsenal-Wolves-August-17-2024-Premier-League",
        "https://fbref.com/en/matches/2c4f8901/Brighton-Everton-August-17-2024-Premier-League",
        "https://fbref.com/en/matches/9d7a2456/Newcastle-Southampton-August-17-2024-Premier-League",
        "https://fbref.com/en/matches/4e6b1890/Nottingham-Forest-Bournemouth-August-17-2024-Premier-League"
    ]
    
    # Generate CSV content
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    
    # Write headers for match data
    csv_writer.writerow([
        'Match_Report_URL', 'Home_Team', 'Away_Team', 'Date', 'Score',
        'Home_Goals', 'Away_Goals', 'Competition', 'Venue'
    ])
    
    # Write match links (ready for future stat extraction)
    for link in demo_links:
        csv_writer.writerow([link, '', '', '', '', '', '', '', ''])
    
    # Add separator and player data headers
    csv_writer.writerow([])  # Empty row separator
    csv_writer.writerow(['=== PLAYER DATA ==='])
    csv_writer.writerow([
        'Match_URL', 'Player_Name', 'Team', 'Position', 'Minutes_Played',
        'Goals', 'Assists', 'Shots', 'Shots_on_Target', 'Passes_Completed',
        'Pass_Accuracy', 'Tackles', 'Interceptions', 'Fouls', 'Cards'
    ])
    
    csv_content = csv_buffer.getvalue()
    csv_buffer.close()
    
    return ScrapingResponse(
        success=True,
        message=f"Demo: Successfully extracted {len(demo_links)} match report links from FBREF fixtures page.",
        links=demo_links,
        csv_data=csv_content
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)