"""
Data Processor - Structures comprehensive data into organized formats
"""

import pandas as pd
from typing import Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        # Updated with correct FBREF data-stat attributes
        self.team_stats_fields = [
            'poss',           # Possession %
            'shots',          # Total Shots
            'shots_on_target', # Shots on Target
            'xg',             # Expected Goals
            'passes',         # Completed Passes
            'pass_pct',       # Pass Completion %
            'crosses',        # Crosses
            'corners',        # Corner Kicks
            'offsides',       # Offsides
            'fouls',          # Fouls
            'cards_yellow',   # Yellow Cards
            'cards_red',      # Red Cards
            'tackles',        # Tackles
            'clearances',     # Clearances
            'saves'           # Saves
        ]
        
        self.player_stats_fields = [
            'minutes',         # Minutes Played
            'goals',           # Goals
            'assists',         # Assists
            'shots_total',     # Shots
            'shots_on_target', # Shots on Target
            'xg',              # Expected Goals
            'xa',              # Expected Assists
            'key_passes',      # Key Passes
            'passes_completed', # Passes Completed
            'passes',          # Pass Attempts
            'tackles',         # Tackles
            'interceptions',   # Interceptions
            'clearances',      # Clearances
            'blocks',          # Blocks
            'fouls',           # Fouls Committed
            'fouled',          # Times Fouled
            'yellow_cards',    # Yellow Cards
            'red_cards'        # Red Cards
        ]
        
        # Keep backward compatibility
        self.passing_stats_fields = [
            'passes_completed', 'passes', 'pass_pct', 'key_passes',
            'crosses'
        ]
        
        self.defensive_stats_fields = [
            'tackles', 'blocks', 'interceptions', 'clearances'
        ]

    def process_comprehensive_data(self, comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process comprehensive data into structured format"""
        
        processed = {
            'match_info': self.extract_match_info(comprehensive_data),
            'team_summary': self.extract_team_summary(comprehensive_data),
            'passing_stats': self.extract_passing_stats(comprehensive_data),
            'defensive_stats': self.extract_defensive_stats(comprehensive_data),
            'player_stats': self.extract_player_stats(comprehensive_data),
            'match_events': self.extract_match_events(comprehensive_data),
            'raw_data': comprehensive_data  # Keep raw data for reference
        }
        
        return processed

    def extract_match_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic match information"""
        
        match_info = {
            'match_url': data.get('metadata', {}).get('match_url', ''),
            'page_title': data.get('metadata', {}).get('page_title', ''),
            'extraction_timestamp': data.get('metadata', {}).get('extraction_timestamp', ''),
            'home_team': '',
            'away_team': '',
            'home_score': 0,
            'away_score': 0,
            'match_date': '',
            'stadium': '',
            'referee': '',
            'attendance': ''
        }
        
        # Extract from page title
        page_title = match_info['page_title']
        if ' vs ' in page_title:
            title_parts = page_title.split(' vs ')
            match_info['home_team'] = title_parts[0].strip()
            if len(title_parts) > 1:
                away_part = title_parts[1].split(' Match Report')[0]
                match_info['away_team'] = away_part.strip()
        
        # Extract from match info boxes
        basic_info = data.get('basic_info', {})
        match_info_box = basic_info.get('match_info_box', {})
        
        for box_data in match_info_box.values():
            text = box_data.get('text', '')
            
            # Extract referee
            if 'Referee:' in text:
                referee_match = re.search(r'Referee:\s*([^,\n]+)', text)
                if referee_match:
                    match_info['referee'] = referee_match.group(1).strip()
            
            # Extract stadium
            if 'Venue:' in text:
                venue_match = re.search(r'Venue:\s*([^,\n]+)', text)
                if venue_match:
                    match_info['stadium'] = venue_match.group(1).strip()
            
            # Extract attendance
            if 'Attendance:' in text:
                attendance_match = re.search(r'Attendance:\s*([0-9,]+)', text)
                if attendance_match:
                    match_info['attendance'] = attendance_match.group(1).strip()
        
        return match_info

    def extract_team_summary(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract team summary statistics - improved to find data anywhere"""
        
        team_stats = []
        all_tables = data.get('all_tables', {})
        
        for table_key, table_data in all_tables.items():
            rows = table_data.get('rows', [])
            
            # Look through all rows for team statistics
            for row in rows:
                data_stat_values = row.get('data_stat_values', {})
                
                # Check if this row has team stats data (look for key team stats fields)
                has_team_stats = any(field in data_stat_values for field in ['poss', 'shots', 'xg', 'passes'])
                
                if has_team_stats and data_stat_values:
                    team_row = {}
                    
                    # Try to identify team name from common fields
                    team_name = ""
                    for possible_team_field in ['team', 'squad', 'club']:
                        if possible_team_field in data_stat_values:
                            team_name = data_stat_values[possible_team_field]
                            break
                    
                    # If no team field found, use table metadata to determine home/away
                    if not team_name:
                        table_metadata = table_data.get('table_metadata', {})
                        table_id = table_metadata.get('id', '').lower()
                        table_class = table_metadata.get('class', '').lower()
                        
                        if 'home' in table_id or 'home' in table_class:
                            team_name = 'home'
                        elif 'away' in table_id or 'away' in table_class:
                            team_name = 'away'
                        else:
                            # Use table headers to identify team
                            headers = table_data.get('headers', [])
                            if headers:
                                header_text = headers[0].get('text', '')
                                if header_text and len(header_text) > 3:  # Likely team name
                                    team_name = header_text
                    
                    team_row['team'] = team_name
                    
                    # Extract all available team stats using correct data-stat names
                    for field in self.team_stats_fields:
                        team_row[field] = data_stat_values.get(field, '')
                    
                    # Only add if we have meaningful data
                    if team_name and any(team_row.get(field) for field in self.team_stats_fields):
                        team_stats.append(team_row)
        
        return team_stats

    def extract_passing_stats(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed passing statistics"""
        
        passing_stats = []
        all_tables = data.get('all_tables', {})
        
        for table_key, table_data in all_tables.items():
            table_id = table_data.get('table_metadata', {}).get('id', '')
            
            # Look for passing stats tables
            if 'passing' in table_id.lower():
                rows = table_data.get('rows', [])
                
                for row in rows:
                    data_stat_values = row.get('data_stat_values', {})
                    
                    if data_stat_values:  # If row has data
                        passing_row = {}
                        
                        # Extract team identifier
                        if 'team' in data_stat_values:
                            passing_row['team'] = data_stat_values.get('team', '')
                        elif 'home' in table_id.lower():
                            passing_row['team'] = 'home'
                        elif 'away' in table_id.lower():
                            passing_row['team'] = 'away'
                        
                        # Extract passing stats
                        for field in self.passing_stats_fields:
                            passing_row[field] = data_stat_values.get(field, '')
                        
                        if passing_row:  # Only add if we have data
                            passing_stats.append(passing_row)
        
        return passing_stats

    def extract_defensive_stats(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract defensive statistics"""
        
        defensive_stats = []
        all_tables = data.get('all_tables', {})
        
        for table_key, table_data in all_tables.items():
            table_id = table_data.get('table_metadata', {}).get('id', '')
            
            # Look for defensive stats tables
            if 'defense' in table_id.lower() or 'defensive' in table_id.lower():
                rows = table_data.get('rows', [])
                
                for row in rows:
                    data_stat_values = row.get('data_stat_values', {})
                    
                    if data_stat_values:
                        defensive_row = {}
                        
                        # Extract team identifier
                        if 'team' in data_stat_values:
                            defensive_row['team'] = data_stat_values.get('team', '')
                        elif 'home' in table_id.lower():
                            defensive_row['team'] = 'home'
                        elif 'away' in table_id.lower():
                            defensive_row['team'] = 'away'
                        
                        # Extract defensive stats
                        for field in self.defensive_stats_fields:
                            defensive_row[field] = data_stat_values.get(field, '')
                        
                        if defensive_row:
                            defensive_stats.append(defensive_row)
        
        return defensive_stats

    def extract_player_stats(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual player statistics - improved to find data anywhere"""
        
        player_stats = []
        all_tables = data.get('all_tables', {})
        
        for table_key, table_data in all_tables.items():
            rows = table_data.get('rows', [])
            
            # Look through all rows for player data
            for row in rows:
                data_stat_values = row.get('data_stat_values', {})
                
                # Check if this row has player data (look for player name field or key player stats)
                has_player_data = ('player' in data_stat_values or 
                                 any(field in data_stat_values for field in ['minutes', 'goals', 'assists']))
                
                if has_player_data and data_stat_values:
                    player_row = {}
                    
                    # Extract player name
                    player_name = ""
                    for possible_name_field in ['player', 'name', 'Player']:
                        if possible_name_field in data_stat_values:
                            player_name = data_stat_values[possible_name_field]
                            break
                    
                    # Skip if no player name (might be team totals row)
                    if not player_name or player_name.lower() in ['total', 'team total', '']:
                        continue
                    
                    player_row['player_name'] = player_name
                    
                    # Determine team from table metadata or headers
                    table_metadata = table_data.get('table_metadata', {})
                    table_id = table_metadata.get('id', '').lower()
                    table_class = table_metadata.get('class', '').lower()
                    
                    team = ""
                    if 'home' in table_id or 'home' in table_class:
                        team = 'home'
                    elif 'away' in table_id or 'away' in table_class:
                        team = 'away'
                    else:
                        # Try to get team from table headers
                        headers = table_data.get('headers', [])
                        if headers:
                            header_text = headers[0].get('text', '')
                            if header_text and len(header_text) > 3:
                                team = header_text
                    
                    player_row['team'] = team
                    player_row['table_source'] = table_key
                    
                    # Extract all available player stats using correct data-stat names
                    for field in self.player_stats_fields:
                        player_row[field] = data_stat_values.get(field, '')
                    
                    # Also extract any other data-stat values that might be useful
                    for key, value in data_stat_values.items():
                        if key not in ['player', 'name', 'Player'] and key not in player_row:
                            player_row[key] = value
                    
                    # Only add if we have meaningful data (player name and at least one stat)
                    if player_name and any(player_row.get(field) for field in self.player_stats_fields):
                        player_stats.append(player_row)
        
        return player_stats

    def extract_match_events(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract match events (goals, cards, substitutions)"""
        
        events = []
        all_tables = data.get('all_tables', {})
        
        for table_key, table_data in all_tables.items():
            table_id = table_data.get('table_metadata', {}).get('id', '')
            
            # Look for events/timeline tables
            if any(keyword in table_id.lower() for keyword in ['events', 'timeline', 'goals', 'cards']):
                rows = table_data.get('rows', [])
                
                for row in rows:
                    data_stat_values = row.get('data_stat_values', {})
                    
                    if data_stat_values:
                        event = {
                            'table_source': table_id,
                            'event_data': data_stat_values
                        }
                        events.append(event)
        
        return events
