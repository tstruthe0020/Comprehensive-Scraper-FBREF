#!/usr/bin/env python3
"""
CSV-based Match Report Scraper
Implements the exact workflow: Fixtures URL -> Match URLs -> CSV -> Scrape Stats -> Update CSV
"""

import asyncio
import pandas as pd
import csv
import io
import logging
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVMatchReportScraper:
    def __init__(self, rate_limit_delay: int = 3, headless: bool = True):
        self.rate_limit_delay = rate_limit_delay
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None

    async def setup_browser(self):
        """Setup browser for scraping"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await context.new_page()
            self.page.set_default_timeout(30000)
            return True
            
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            return False

    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    async def extract_match_urls_from_fixtures(self, fixtures_url: str) -> List[str]:
        """
        Step 1: Extract match report URLs from fixtures/results page
        """
        try:
            logger.info(f"Extracting match URLs from: {fixtures_url}")
            
            await self.page.goto(fixtures_url, wait_until='networkidle', timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find the score column using multiple strategies
            score_header = None
            
            # Strategy 1: Look for data-stat="score"
            score_header = soup.find('th', {'data-stat': 'score'})
            
            # Strategy 2: Look for text "Score"
            if not score_header:
                score_header = soup.find('th', string=re.compile(r'Score', re.IGNORECASE))
            
            if not score_header:
                logger.error("Could not find Score column")
                return []
            
            # Find the table and get score column index
            table = score_header.find_parent('table')
            if not table:
                logger.error("Could not find table")
                return []
            
            headers_row = score_header.find_parent('tr')
            headers = headers_row.find_all(['th', 'td'])
            score_column_index = None
            
            for i, header in enumerate(headers):
                if (header.get('data-stat') == 'score' or 
                    (header.get_text(strip=True).lower() == 'score')):
                    score_column_index = i
                    break
            
            if score_column_index is None:
                logger.error("Could not determine score column position")
                return []
            
            # Extract match report links
            match_links = []
            tbody = table.find('tbody')
            
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) > score_column_index:
                        score_cell = cells[score_column_index]
                        links = score_cell.find_all('a', href=True)
                        for link in links:
                            href = link['href']
                            if '/matches/' in href:
                                full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                                if full_url not in match_links:
                                    match_links.append(full_url)
            
            logger.info(f"Found {len(match_links)} match URLs")
            return match_links
            
        except Exception as e:
            logger.error(f"Error extracting match URLs: {e}")
            return []

    def create_initial_csv(self, match_urls: List[str]) -> str:
        """
        Step 2: Create initial CSV with match URLs
        """
        try:
            # Create CSV structure
            csv_data = []
            
            for i, url in enumerate(match_urls, 1):
                # Extract basic info from URL
                match_info = self.extract_basic_info_from_url(url)
                
                row = {
                    'Match_Number': i,
                    'Match_URL': url,
                    'Home_Team': match_info.get('home_team', ''),
                    'Away_Team': match_info.get('away_team', ''),
                    'Date': match_info.get('date', ''),
                    'Competition': match_info.get('competition', ''),
                    
                    # Team stats (to be populated)
                    'Home_Possession': '',
                    'Away_Possession': '',
                    'Home_Shots': '',
                    'Away_Shots': '',
                    'Home_Shots_On_Target': '',
                    'Away_Shots_On_Target': '',
                    'Home_Fouls': '',
                    'Away_Fouls': '',
                    'Home_Yellow_Cards': '',
                    'Away_Yellow_Cards': '',
                    'Home_Red_Cards': '',
                    'Away_Red_Cards': '',
                    'Home_Corners': '',
                    'Away_Corners': '',
                    'Final_Score': '',
                    'Referee': '',
                    'Stadium': '',
                    'Attendance': '',
                    
                    # Top scorers (to be populated)
                    'Top_Scorer_Name': '',
                    'Top_Scorer_Team': '',
                    'Top_Scorer_Goals': '',
                    'Top_Assists_Name': '',
                    'Top_Assists_Team': '',
                    'Top_Assists_Count': '',
                    
                    # Status
                    'Scraped': 'No',
                    'Scrape_Timestamp': '',
                    'Scrape_Error': ''
                }
                
                csv_data.append(row)
            
            # Convert to CSV string
            output = io.StringIO()
            if csv_data:
                fieldnames = list(csv_data[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"Created initial CSV with {len(csv_data)} matches")
            return csv_content
            
        except Exception as e:
            logger.error(f"Error creating CSV: {e}")
            return ""

    def extract_basic_info_from_url(self, url: str) -> Dict[str, str]:
        """Extract basic match info from URL"""
        try:
            # Example: https://fbref.com/en/matches/eac7c00b/West-Ham-United-Aston-Villa-August-17-2024-Premier-League
            parts = url.split('/')
            if len(parts) > 5:
                match_info_part = parts[-1]
                info_parts = match_info_part.split('-')
                
                # Find date (look for year)
                date_idx = None
                for i, part in enumerate(info_parts):
                    if len(part) == 4 and part.isdigit() and part.startswith('20'):
                        date_idx = i
                        break
                
                if date_idx and date_idx >= 3:
                    # Extract teams
                    team_parts = info_parts[:date_idx-2]
                    mid_point = len(team_parts) // 2
                    home_team = team_parts[0] if len(team_parts) > 0 else "Unknown"
                    away_team = team_parts[mid_point] if len(team_parts) > mid_point else "Unknown"
                    
                    # Extract date
                    if date_idx >= 2:
                        month = info_parts[date_idx-2]
                        day = info_parts[date_idx-1]
                        year = info_parts[date_idx]
                        date = f"{month}-{day}-{year}"
                    else:
                        date = "Unknown"
                    
                    # Extract competition
                    competition = "-".join(info_parts[date_idx+1:]) if date_idx+1 < len(info_parts) else "Unknown"
                    
                    return {
                        'home_team': home_team.replace('-', ' '),
                        'away_team': away_team.replace('-', ' '),
                        'date': date,
                        'competition': competition.replace('-', ' ')
                    }
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
        
        return {'home_team': 'Unknown', 'away_team': 'Unknown', 'date': 'Unknown', 'competition': 'Unknown'}

    async def scrape_team_and_player_stats(self, match_url: str) -> Dict[str, Any]:
        """
        Step 3: Scrape team and player statistics from match report page
        """
        try:
            logger.info(f"Scraping stats from: {match_url}")
            
            await self.page.goto(match_url, wait_until='domcontentloaded', timeout=30000)
            await self.page.wait_for_timeout(3000)
            
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            stats = {
                'match_info': {},
                'team_stats': {},
                'player_stats': []
            }
            
            # Extract basic match info
            stats['match_info'] = await self.extract_match_info_from_page(soup)
            
            # Extract team statistics from team stats tables
            stats['team_stats'] = await self.extract_team_stats_from_tables(soup)
            
            # Extract top player stats
            stats['player_stats'] = await self.extract_top_player_stats(soup)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error scraping match stats: {e}")
            return {}

    async def extract_match_info_from_page(self, soup) -> Dict[str, Any]:
        """Extract basic match information from page"""
        match_info = {}
        
        try:
            # Extract from scorebox
            scorebox = soup.find('div', class_='scorebox')
            if scorebox:
                # Extract score
                scores = scorebox.find_all('div', class_='score')
                if len(scores) >= 2:
                    home_score = scores[0].get_text(strip=True)
                    away_score = scores[1].get_text(strip=True)
                    match_info['final_score'] = f"{home_score}-{away_score}"
            
            # Extract metadata (referee, stadium, attendance)
            meta_divs = soup.find_all('div', {'class': re.compile(r'meta|info')})
            for div in meta_divs:
                text = div.get_text()
                
                if 'Referee:' in text:
                    referee_match = re.search(r'Referee:\s*([^,\n]+)', text)
                    if referee_match:
                        match_info['referee'] = referee_match.group(1).strip()
                
                if 'Venue:' in text:
                    venue_match = re.search(r'Venue:\s*([^,\n]+)', text)
                    if venue_match:
                        match_info['stadium'] = venue_match.group(1).strip()
                
                if 'Attendance:' in text:
                    attendance_match = re.search(r'Attendance:\s*([0-9,]+)', text)
                    if attendance_match:
                        match_info['attendance'] = attendance_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"Error extracting match info: {e}")
        
        return match_info

    async def extract_team_stats_from_tables(self, soup) -> Dict[str, Any]:
        """Extract team statistics from stats tables - IMPROVED VERSION"""
        team_stats = {}
        
        try:
            # Find all tables
            tables = soup.find_all('table')
            
            for table in tables:
                # Look for the team comparison table
                headers = table.find_all('th')
                header_texts = [th.get_text(strip=True).lower() for th in headers]
                
                # Check if this looks like the team comparison table
                if len(header_texts) >= 3:
                    # Look for pattern: [team1, team2, stat1, stat2, ...]
                    potential_teams = header_texts[:2]
                    potential_stats = header_texts[2:]
                    
                    # Check if we have team-like names and stats-like names
                    has_team_indicators = any(word in ' '.join(potential_teams) for word in ['united', 'manchester', 'fulham', 'chelsea', 'arsenal', 'liverpool', 'city', 'ham', 'villa', 'spurs', 'wolves'])
                    has_stat_indicators = any(word in ' '.join(potential_stats) for word in ['possession', 'shots', 'passing', 'accuracy', 'saves', 'cards', 'fouls'])
                    
                    if has_team_indicators and has_stat_indicators:
                        # Extract the data from this table
                        tbody = table.find('tbody')
                        if tbody:
                            rows = tbody.find_all('tr')
                            
                            # Initialize team stats
                            team1_name = potential_teams[0].title()
                            team2_name = potential_teams[1].title()
                            team_stats[team1_name] = {}
                            team_stats[team2_name] = {}
                            
                            current_stat = None
                            
                            for row in rows:
                                cells = row.find_all(['td', 'th'])
                                cell_texts = [cell.get_text(strip=True) for cell in cells]
                                
                                if len(cell_texts) == 1:
                                    # This is a stat name row
                                    current_stat = cell_texts[0].lower().replace(' ', '_')
                                elif len(cell_texts) == 2 and current_stat:
                                    # This is a data row with two values
                                    team1_value = cell_texts[0]
                                    team2_value = cell_texts[1]
                                    
                                    # Clean up values (extract percentages, numbers)
                                    team1_clean = self.extract_key_value(team1_value, current_stat)
                                    team2_clean = self.extract_key_value(team2_value, current_stat)
                                    
                                    # Store the values
                                    team_stats[team1_name][current_stat] = team1_clean
                                    team_stats[team2_name][current_stat] = team2_clean
                        
                        break  # Found our table, stop looking
            
        except Exception as e:
            logger.error(f"Error extracting team stats: {e}")
        
        return team_stats

    def extract_key_value(self, value_text: str, stat_name: str) -> str:
        """Extract the most relevant value from complex stat text"""
        try:
            if not value_text:
                return ""
            
            # For possession, extract percentage
            if 'possession' in stat_name:
                pct_match = re.search(r'(\d+)%', value_text)
                if pct_match:
                    return pct_match.group(1)
            
            # For accuracy stats, extract percentage
            elif 'accuracy' in stat_name:
                pct_match = re.search(r'(\d+)%', value_text)
                if pct_match:
                    return pct_match.group(1)
            
            # For shots on target, extract first number (shots on target)
            elif 'shots' in stat_name:
                shot_match = re.search(r'(\d+)\s*of\s*\d+', value_text)
                if shot_match:
                    return shot_match.group(1)
            
            # For saves, extract first number
            elif 'saves' in stat_name:
                save_match = re.search(r'(\d+)\s*of\s*\d+', value_text)
                if save_match:
                    return save_match.group(1)
            
            # For other stats, just extract first number
            else:
                num_match = re.search(r'(\d+)', value_text)
                if num_match:
                    return num_match.group(1)
            
            # Fallback: return original value
            return value_text
            
        except Exception as e:
            logger.error(f"Error extracting value from '{value_text}': {e}")
            return value_text

    async def extract_top_player_stats(self, soup) -> List[Dict[str, Any]]:
        """Extract top player statistics"""
        player_stats = []
        
        try:
            # Look for player stats tables
            tables = soup.find_all('table')
            
            for table in tables:
                # Check if this is a player stats table
                headers = table.find_all('th')
                header_data_stats = [th.get('data-stat', '') for th in headers]
                
                # Look for player-specific data-stats
                if any(stat in header_data_stats for stat in ['player', 'minutes', 'goals', 'assists']):
                    tbody = table.find('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        
                        for row in rows[:10]:  # Top 10 players
                            cells = row.find_all(['td', 'th'])
                            player_data = {}
                            
                            for cell in cells:
                                data_stat = cell.get('data-stat', '')
                                value = cell.get_text(strip=True)
                                
                                if data_stat and value:
                                    player_data[data_stat] = value
                            
                            if 'player' in player_data:
                                player_stats.append(player_data)
            
        except Exception as e:
            logger.error(f"Error extracting player stats: {e}")
        
        return player_stats

    def update_csv_with_stats(self, csv_content: str, match_url: str, stats: Dict[str, Any]) -> str:
        """
        Step 4: Update CSV with scraped team and player statistics
        """
        try:
            # Read CSV
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Find the row for this match
            match_row_idx = df[df['Match_URL'] == match_url].index
            
            if len(match_row_idx) == 0:
                logger.warning(f"Match URL not found in CSV: {match_url}")
                return csv_content
            
            idx = match_row_idx[0]
            
            # Update with match info
            match_info = stats.get('match_info', {})
            if 'final_score' in match_info:
                df.at[idx, 'Final_Score'] = match_info['final_score']
            if 'referee' in match_info:
                df.at[idx, 'Referee'] = match_info['referee']
            if 'stadium' in match_info:
                df.at[idx, 'Stadium'] = match_info['stadium']
            if 'attendance' in match_info:
                df.at[idx, 'Attendance'] = match_info['attendance']
            
            # Update with team stats using improved mapping
            team_stats = stats.get('team_stats', {})
            teams = list(team_stats.keys())
            
            if len(teams) >= 2:
                home_team_stats = team_stats.get(teams[0], {})
                away_team_stats = team_stats.get(teams[1], {})
                
                # Map team stats to CSV columns using the new stat names
                stat_mapping = {
                    'possession': ['Home_Possession', 'Away_Possession'],
                    'shots_on_target': ['Home_Shots_On_Target', 'Away_Shots_On_Target'],
                    'passing_accuracy': ['Home_Pass_Accuracy', 'Away_Pass_Accuracy'],
                    'saves': ['Home_Saves', 'Away_Saves'],
                    'cards': ['Home_Cards', 'Away_Cards']
                }
                
                for stat_key, col_names in stat_mapping.items():
                    if stat_key in home_team_stats:
                        df.at[idx, col_names[0]] = home_team_stats[stat_key]
                    if stat_key in away_team_stats:
                        df.at[idx, col_names[1]] = away_team_stats[stat_key]
            
            # Update with top player stats
            player_stats = stats.get('player_stats', [])
            if player_stats:
                # Find top scorer
                top_scorer = max(player_stats, 
                               key=lambda p: int(p.get('goals', '0') or '0'), 
                               default={})
                if top_scorer.get('goals', '0') != '0':
                    df.at[idx, 'Top_Scorer_Name'] = top_scorer.get('player', '')
                    df.at[idx, 'Top_Scorer_Goals'] = top_scorer.get('goals', '')
                
                # Find top assists
                top_assists = max(player_stats, 
                                key=lambda p: int(p.get('assists', '0') or '0'), 
                                default={})
                if top_assists.get('assists', '0') != '0':
                    df.at[idx, 'Top_Assists_Name'] = top_assists.get('player', '')
                    df.at[idx, 'Top_Assists_Count'] = top_assists.get('assists', '')
            
            # Update status
            df.at[idx, 'Scraped'] = 'Yes'
            df.at[idx, 'Scrape_Timestamp'] = datetime.now().isoformat()
            df.at[idx, 'Scrape_Error'] = ''
            
            # Convert back to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            updated_csv = output.getvalue()
            output.close()
            
            return updated_csv
            
        except Exception as e:
            logger.error(f"Error updating CSV: {e}")
            # Update with error status
            try:
                df = pd.read_csv(io.StringIO(csv_content))
                match_row_idx = df[df['Match_URL'] == match_url].index
                if len(match_row_idx) > 0:
                    idx = match_row_idx[0]
                    df.at[idx, 'Scraped'] = 'Error'
                    df.at[idx, 'Scrape_Error'] = str(e)
                    df.at[idx, 'Scrape_Timestamp'] = datetime.now().isoformat()
                    
                    output = io.StringIO()
                    df.to_csv(output, index=False)
                    updated_csv = output.getvalue()
                    output.close()
                    return updated_csv
            except:
                pass
            
            return csv_content

    async def full_workflow(self, fixtures_urls: List[str], max_matches: int = None) -> str:
        """
        Complete workflow: Fixtures -> URLs -> CSV -> Stats -> Updated CSV
        """
        try:
            if not await self.setup_browser():
                raise Exception("Failed to setup browser")
            
            all_match_urls = []
            
            # Step 1: Extract match URLs from all fixtures pages
            for fixtures_url in fixtures_urls:
                match_urls = await self.extract_match_urls_from_fixtures(fixtures_url)
                all_match_urls.extend(match_urls)
                
                # Rate limiting between fixtures pages
                await asyncio.sleep(self.rate_limit_delay)
            
            # Remove duplicates and limit if specified
            all_match_urls = list(dict.fromkeys(all_match_urls))  # Remove duplicates
            if max_matches:
                all_match_urls = all_match_urls[:max_matches]
            
            logger.info(f"Processing {len(all_match_urls)} total matches")
            
            # Step 2: Create initial CSV
            csv_content = self.create_initial_csv(all_match_urls)
            
            # Step 3 & 4: Scrape stats for each match and update CSV
            for i, match_url in enumerate(all_match_urls):
                try:
                    logger.info(f"Processing match {i+1}/{len(all_match_urls)}: {match_url}")
                    
                    # Scrape stats
                    stats = await self.scrape_team_and_player_stats(match_url)
                    
                    # Update CSV
                    csv_content = self.update_csv_with_stats(csv_content, match_url, stats)
                    
                    # Rate limiting between matches
                    if i < len(all_match_urls) - 1:
                        await asyncio.sleep(self.rate_limit_delay)
                        
                except Exception as e:
                    logger.error(f"Error processing match {match_url}: {e}")
                    # Continue with next match
                    continue
            
            return csv_content
            
        finally:
            await self.cleanup()