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
        }
        
        # Use session for better connection handling
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(request.url, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the Score column header
        score_header = soup.find('th', {
            'aria-label': 'Score',
            'data-stat': 'score',
            'scope': 'col'
        })
        
        if not score_header:
            return ScrapingResponse(
                success=False,
                message="Could not find the Score column in the table. Please check if the URL contains fixture/schedule data.",
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
            if header.get('data-stat') == 'score':
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
            return ScrapingResponse(
                success=False,
                message="No match report links found in the Score column. The page might not contain completed fixtures.",
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

@app.get("/api/download-csv/{filename}")
async def download_csv(filename: str, csv_data: str):
    def generate():
        yield csv_data
    
    return StreamingResponse(
        io.BytesIO(csv_data.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)