"""
CSV Handler - Reads input URLs and saves organized results
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

class CSVHandler:
    def __init__(self):
        pass
    
    def read_urls_from_csv(self, csv_file: str, url_column: str = 'match_url') -> List[str]:
        """Read match URLs from CSV file"""
        
        try:
            df = pd.read_csv(csv_file)
            
            if url_column not in df.columns:
                logger.error(f"Column '{url_column}' not found in CSV. Available columns: {list(df.columns)}")
                return []
            
            urls = df[url_column].dropna().tolist()
            logger.info(f"Successfully read {len(urls)} URLs from CSV")
            
            return urls
            
        except Exception as e:
            logger.error(f"Error reading CSV file {csv_file}: {e}")
            return []
    
    def save_results_to_csv(self, results: List[Dict[str, Any]], output_dir: Path, season: str):
        """Save scraping results to multiple CSV files"""
        
        try:
            # Separate successful results from errors
            successful_results = [r for r in results if 'error' not in r]
            error_results = [r for r in results if 'error' in r]
            
            if successful_results:
                # 1. Match Information
                match_info_data = [r.get('match_info', {}) for r in successful_results]
                if match_info_data:
                    match_info_df = pd.DataFrame(match_info_data)
                    match_info_file = output_dir / f"{season}_match_info.csv"
                    match_info_df.to_csv(match_info_file, index=False)
                    logger.info(f"Saved match info to: {match_info_file}")
                
                # 2. Team Summary Statistics
                team_summary_data = []
                for result in successful_results:
                    match_url = result.get('match_info', {}).get('match_url', '')
                    for team_stat in result.get('team_summary', []):
                        team_stat['match_url'] = match_url
                        team_summary_data.append(team_stat)
                
                if team_summary_data:
                    team_summary_df = pd.DataFrame(team_summary_data)
                    team_summary_file = output_dir / f"{season}_team_summary.csv"
                    team_summary_df.to_csv(team_summary_file, index=False)
                    logger.info(f"Saved team summary to: {team_summary_file}")
                
                # 3. Passing Statistics
                passing_stats_data = []
                for result in successful_results:
                    match_url = result.get('match_info', {}).get('match_url', '')
                    for passing_stat in result.get('passing_stats', []):
                        passing_stat['match_url'] = match_url
                        passing_stats_data.append(passing_stat)
                
                if passing_stats_data:
                    passing_stats_df = pd.DataFrame(passing_stats_data)
                    passing_stats_file = output_dir / f"{season}_passing_stats.csv"
                    passing_stats_df.to_csv(passing_stats_file, index=False)
                    logger.info(f"Saved passing stats to: {passing_stats_file}")
                
                # 4. Defensive Statistics
                defensive_stats_data = []
                for result in successful_results:
                    match_url = result.get('match_info', {}).get('match_url', '')
                    for defensive_stat in result.get('defensive_stats', []):
                        defensive_stat['match_url'] = match_url
                        defensive_stats_data.append(defensive_stat)
                
                if defensive_stats_data:
                    defensive_stats_df = pd.DataFrame(defensive_stats_data)
                    defensive_stats_file = output_dir / f"{season}_defensive_stats.csv"
                    defensive_stats_df.to_csv(defensive_stats_file, index=False)
                    logger.info(f"Saved defensive stats to: {defensive_stats_file}")
                
                # 5. Player Statistics
                player_stats_data = []
                for result in successful_results:
                    match_url = result.get('match_info', {}).get('match_url', '')
                    for player_stat in result.get('player_stats', []):
                        player_stat['match_url'] = match_url
                        player_stats_data.append(player_stat)
                
                if player_stats_data:
                    player_stats_df = pd.DataFrame(player_stats_data)
                    player_stats_file = output_dir / f"{season}_player_stats.csv"
                    player_stats_df.to_csv(player_stats_file, index=False)
                    logger.info(f"Saved player stats to: {player_stats_file}")
                
                # 6. Match Events
                events_data = []
                for result in successful_results:
                    match_url = result.get('match_info', {}).get('match_url', '')
                    for event in result.get('match_events', []):
                        event_flat = {'match_url': match_url, 'table_source': event.get('table_source', '')}
                        event_flat.update(event.get('event_data', {}))
                        events_data.append(event_flat)
                
                if events_data:
                    events_df = pd.DataFrame(events_data)
                    events_file = output_dir / f"{season}_match_events.csv"
                    events_df.to_csv(events_file, index=False)
                    logger.info(f"Saved match events to: {events_file}")
                
                # 7. Complete Raw Data (JSON format for complex data)
                raw_data_file = output_dir / f"{season}_raw_data.json"
                with open(raw_data_file, 'w') as f:
                    json.dump(successful_results, f, indent=2, default=str)
                logger.info(f"Saved raw data to: {raw_data_file}")
            
            # Save error log
            if error_results:
                error_df = pd.DataFrame(error_results)
                error_file = output_dir / f"{season}_errors.csv"
                error_df.to_csv(error_file, index=False)
                logger.info(f"Saved errors to: {error_file}")
            
            # Create summary report
            self.create_summary_report(successful_results, error_results, output_dir, season)
            
        except Exception as e:
            logger.error(f"Error saving results to CSV: {e}")
    
    def create_summary_report(self, successful_results: List[Dict], error_results: List[Dict], 
                            output_dir: Path, season: str):
        """Create a summary report of the scraping session"""
        
        summary = {
            'season': season,
            'total_matches_attempted': len(successful_results) + len(error_results),
            'successful_extractions': len(successful_results),
            'failed_extractions': len(error_results),
            'success_rate': f"{(len(successful_results) / (len(successful_results) + len(error_results)) * 100):.1f}%" if (successful_results or error_results) else "0%",
            'total_data_points': sum(r.get('raw_data', {}).get('metadata', {}).get('total_data_points', 0) for r in successful_results),
            'average_tables_per_match': f"{sum(r.get('raw_data', {}).get('metadata', {}).get('total_tables_found', 0) for r in successful_results) / len(successful_results):.1f}" if successful_results else "0",
            'files_created': [
                f"{season}_match_info.csv",
                f"{season}_team_summary.csv", 
                f"{season}_passing_stats.csv",
                f"{season}_defensive_stats.csv",
                f"{season}_player_stats.csv",
                f"{season}_match_events.csv",
                f"{season}_raw_data.json"
            ]
        }
        
        summary_df = pd.DataFrame([summary])
        summary_file = output_dir / f"{season}_scraping_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        
        logger.info(f"Created summary report: {summary_file}")
        logger.info(f"SCRAPING SUMMARY: {summary['successful_extractions']}/{summary['total_matches_attempted']} matches successful ({summary['success_rate']})")
