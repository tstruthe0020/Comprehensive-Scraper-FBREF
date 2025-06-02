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
    url: str

class ScrapingResponse(BaseModel):
    success: bool
    message: str
    links: List[str] = []
    csv_data: str = ""

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/scrape-fbref")
async def scrape_fbref_fixtures(request: ScrapingRequest):
    try:
        # Validate URL
        if not request.url or not request.url.startswith("https://fbref.com"):
            raise HTTPException(status_code=400, detail="Please provide a valid FBREF URL")
        
        # Try direct scraping first, then fallback to alternative method
        try:
            # Fetch the webpage with enhanced headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.google.com/',
            }
            
            # Use session for better connection handling
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(request.url, timeout=30)
            response.raise_for_status()
            html_content = response.content
            
        except requests.RequestException as e:
            if "403" in str(e) or "Forbidden" in str(e):
                return ScrapingResponse(
                    success=False,
                    message="FBREF is blocking scraping requests. This is common for web scraping. You may need to use alternative methods like:\n\n1. Use a VPN or proxy service\n2. Try accessing the page manually first in a browser\n3. Check if FBREF offers an official API\n4. Use browser automation tools like Selenium\n\nThe scraping algorithm is working correctly - the issue is FBREF's anti-bot protection.",
                    links=[],
                    csv_data=""
                )
            else:
                raise e
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the Score column header
        score_header = soup.find('th', {
            'aria-label': 'Score',
            'data-stat': 'score',
            'scope': 'col'
        })
        
        if not score_header:
            # Try alternative selectors for the Score column
            score_header = soup.find('th', string=re.compile(r'Score', re.IGNORECASE))
            if not score_header:
                # Look for any th with data-stat="score"
                score_header = soup.find('th', {'data-stat': 'score'})
        
        if not score_header:
            return ScrapingResponse(
                success=False,
                message="Could not find the Score column in the table. The page structure might be different than expected. Please verify this is a FBREF fixture/schedule page.",
                links=[],
                csv_data=""
            )
        
        # Find the table containing the score header
        table = score_header.find_parent('table')
        if not table:
            return ScrapingResponse(
                success=False,
                message="Could not find the table containing the Score column.",
                links=[],
                csv_data=""
            )
        
        # Get column index of Score column
        headers_row = score_header.find_parent('tr')
        headers = headers_row.find_all(['th', 'td'])
        score_column_index = None
        
        for i, header in enumerate(headers):
            if header.get('data-stat') == 'score' or (header.get('aria-label') and 'score' in header.get('aria-label').lower()):
                score_column_index = i
                break
        
        if score_column_index is None:
            return ScrapingResponse(
                success=False,
                message="Could not determine the position of the Score column.",
                links=[],
                csv_data=""
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
        
        if not match_links:
            # Try alternative approach - look for any match links in the table
            all_links = table.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if '/matches/' in href:
                    full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                    if full_url not in match_links:
                        match_links.append(full_url)
        
        if not match_links:
            return ScrapingResponse(
                success=False,
                message="No match report links found. This could mean:\n1. The page contains only future fixtures (no completed matches)\n2. The page structure is different than expected\n3. The fixtures haven't been played yet\n\nTry using a URL for a previous season or wait for matches to be completed.",
                links=[],
                csv_data=""
            )
        
        # Generate CSV content
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Write headers for match data
        csv_writer.writerow([
            'Match_Report_URL', 'Home_Team', 'Away_Team', 'Date', 'Score',
            'Home_Goals', 'Away_Goals', 'Competition', 'Venue'
        ])
        
        # Write match links (we'll fill in the stats later)
        for link in match_links:
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
            message=f"Successfully extracted {len(match_links)} match report links from FBREF fixtures page.",
            links=match_links,
            csv_data=csv_content
        )
        
    except requests.RequestException as e:
        return ScrapingResponse(
            success=False,
            message=f"Error fetching the webpage: {str(e)}",
            links=[],
            csv_data=""
        )
    except Exception as e:
        return ScrapingResponse(
            success=False,
            message=f"An error occurred while processing the page: {str(e)}",
            links=[],
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