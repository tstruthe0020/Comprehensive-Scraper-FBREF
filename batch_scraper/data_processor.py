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
        self.team_stats_fields = [
            'possession', 'shots_total', 'shots_on_target', 'expected_goals',
            'passes_completed', 'passes', 'passes_pct', 'key_passes',
            'tackles_won', 'tackles', 'blocks', 'interceptions', 'clearances',
            'fouls', 'cards_yellow', 'cards_red', 'corners', 'offsides'
        ]
        
        self.passing_stats_fields = [
            'passes_completed', 'passes', 'passes_pct', 'passes_short_completed',
            'passes_medium_completed', 'passes_long_completed', 'key_passes',
            'passes_into_final_third', 'passes_into_penalty_area', 'crosses_completed'
        ]
        
        self.defensive_stats_fields = [
            'tackles_won', 'tackles', 'tackles_won_pct', 'blocks', 'interceptions',
            'clearances', 'aerial_duels_won', 'aerial_duels'
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
        """Extract team summary statistics"""
        
        team_stats = []
        all_tables = data.get('all_tables', {})
        
        for table_key, table_data in all_tables.items():
            table_id = table_data.get('table_metadata', {}).get('id', '')
            
            # Look for team stats table
            if 'team_stats' in table_id or 'summary' in table_id:
                rows = table_data.get('rows', [])
                
                for row in rows:
                    data_stat_values = row.get('data_stat_values', {})
                    
                    if 'team' in data_stat_values:
                        team_row = {'team': data_stat_values.get('team', '')}
                        
                        # Extract all available team stats
                        for field in self.team_stats_fields:
                            team_row[field] = data_stat_values.get(field, '')
                        
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
        """Extract individual player statistics"""
        
        player_stats = []
        all_tables = data.get('all_tables', {})
        
        for table_key, table_data in all_tables.items():
            table_id = table_data.get('table_metadata', {}).get('id', '')
            
            # Look for player/lineup tables
            if 'lineup' in table_id.lower() or 'player' in table_id.lower():
                rows = table_data.get('rows', [])
                
                for row in rows:
                    data_stat_values = row.get('data_stat_values', {})
                    
                    if 'player' in data_stat_values:
                        player_row = {
                            'player_name': data_stat_values.get('player', ''),
                            'team': 'home' if 'home' in table_id.lower() else 'away',
                            'table_source': table_id
                        }
                        
                        # Extract all available player stats
                        for key, value in data_stat_values.items():
                            if key != 'player':
                                player_row[key] = value
                        
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
